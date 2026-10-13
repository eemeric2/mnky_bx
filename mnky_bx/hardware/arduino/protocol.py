# mnky_bx/hardware/arduino/protocol.py
"""
Communication protocol for Arduino Uno
Handles serial communication, error checking, retries
"""

import serial
import time
from typing import Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ArduinoProtocol:
    """
    Low-level Arduino communication protocol
    Handles serial encoding/decoding, timeouts, retries
    """
    
    # Protocol constants
    BAUD_RATE = 115200
    TIMEOUT = 1.0          # seconds
    MAX_RETRIES = 3
    RETRY_DELAY = 0.5      # seconds
    
    def __init__(self, port: str, baud_rate: int = BAUD_RATE):
        """
        Initialize serial connection
        
        Args:
            port: Serial port (e.g., 'COM4', '/dev/ttyACM0')
            baud_rate: Communication speed (default 115200 for GRBL)
        """
        self.port = port
        self.baud_rate = baud_rate
        self.serial_connection = None
        self.is_connected = False
    
    def connect(self, timeout_s: float = 5.0) -> bool:
        """
        Establish connection to Arduino
        
        Args:
            timeout_s: How long to wait for handshake
        
        Returns:
            True if successful connection
        """
        try:
            logger.info(f"Connecting to Arduino on {self.port}...")
            
            self.serial_connection = serial.Serial(
                self.port,
                self.baud_rate,
                timeout=self.TIMEOUT
            )
            
            # Wait for GRBL handshake
            start_time = time.time()
            while time.time() - start_time < timeout_s:
                if self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.readline().decode('utf-8').strip()
                    logger.debug(f"Received: {data}")
                    
                    if "Grbl 1.1h" in data:
                        self.is_connected = True
                        logger.info("Arduino connected and ready!")
                        return True
                
                time.sleep(0.1)
            
            logger.error("Arduino handshake timeout")
            return False
        
        except Exception as e:
            logger.error(f"Failed to connect to Arduino: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from Arduino"""
        if self.serial_connection:
            self.serial_connection.close()
            self.is_connected = False
            logger.info("Arduino disconnected")
    
    def send_command(self, command: str, wait_for_response: bool = True) -> Optional[str]:
        """
        Send command to Arduino
        
        Args:
            command: Command string (e.g., "G0 X5\n")
            wait_for_response: Whether to wait for "ok" response
        
        Returns:
            Response from Arduino or None
        """
        if not self.is_connected:
            logger.error("Arduino not connected")
            return None
        
        try:
            # Ensure command ends with newline
            if not command.endswith('\n'):
                command += '\n'
            
            logger.debug(f"Sending: {command.strip()}")
            self.serial_connection.write(command.encode('utf-8'))
            
            if wait_for_response:
                response = self.read_response()
                return response
            
            return None
        
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return None
    
    def read_response(self, timeout_s: float = None) -> Optional[str]:
        """
        Read response from Arduino with timeout
        
        Args:
            timeout_s: How long to wait for response
        
        Returns:
            Response string or None if timeout
        """
        if timeout_s is None:
            timeout_s = self.TIMEOUT
        
        start_time = time.time()
        
        while time.time() - start_time < timeout_s:
            if self.serial_connection.in_waiting > 0:
                try:
                    data = self.serial_connection.readline().decode('utf-8').strip()
                    logger.debug(f"Received: {data}")
                    return data
                except Exception as e:
                    logger.error(f"Error reading response: {e}")
                    return None
            
            time.sleep(0.01)
        
        logger.warning(f"Response timeout after {timeout_s}s")
        return None
    
    def send_command_with_retry(self, command: str, 
                               expected_response: str = "ok",
                               max_retries: int = None) -> bool:
        """
        Send command with automatic retry on failure
        
        Args:
            command: Command to send
            expected_response: What response indicates success
            max_retries: Number of retries (default MAX_RETRIES)
        
        Returns:
            True if successful
        """
        if max_retries is None:
            max_retries = self.MAX_RETRIES
        
        for attempt in range(max_retries):
            try:
                response = self.send_command(command, wait_for_response=True)
                
                if response and expected_response.lower() in response.lower():
                    logger.info(f"Command successful (attempt {attempt + 1})")
                    return True
                
                if attempt < max_retries - 1:
                    logger.warning(f"Retry {attempt + 1}/{max_retries}...")
                    time.sleep(self.RETRY_DELAY)
            
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
        
        logger.error(f"Command failed after {max_retries} attempts")
        return False
    
    def flush_buffer(self) -> None:
        """Clear any pending data in serial buffer"""
        if self.serial_connection:
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()