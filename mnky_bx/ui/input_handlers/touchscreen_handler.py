# mnky_bx/ui/input_handlers/touchscreen_handler.py
"""
Touchscreen input handler
Maps clicks to left/right regions or custom UI elements
"""

import pygame
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ClickRegion:
    """Clickable region on screen"""
    name: str  # 'left', 'right', 'button_0', etc.
    rect: pygame.Rect  # Region bounds
    event_type: str  # Event to trigger


class TouchscreenHandler:
    """Handles touchscreen clicks via pygame mouse events"""

    def __init__(self, config: Dict):
        """
        Initialize touchscreen handler

        Args:
            config: Touchscreen configuration dict with:
                - screen_width, screen_height
                - regions: List of clickable regions
                - split_screen: bool (True = left/right halves, False = use custom regions)
        """
        self.config = config
        self.regions: List[ClickRegion] = []
        self.last_click_time = None
        self.debounce_ms = config.get('debounce_ms', 100)  # Prevent double-clicks

        # Setup default regions or custom ones
        self._setup_regions()

    def _setup_regions(self) -> None:
        """Setup clickable regions"""
        width = self.config.get('screen_width', 1920)
        height = self.config.get('screen_height', 1080)

        if self.config.get('split_screen', True):
            # Simple left/right split
            left_rect = pygame.Rect(0, 0, width // 2, height)
            right_rect = pygame.Rect(width // 2, 0, width // 2, height)

            self.regions = [
                ClickRegion('left', left_rect, 'left_pressed'),
                ClickRegion('right', right_rect, 'right_pressed'),
            ]

            logger.info(f"Touchscreen split-screen mode: "
                        f"left={left_rect}, right={right_rect}")

        else:
            # Custom regions from config
            custom_regions = self.config.get('regions', [])
            for region_config in custom_regions:
                rect = pygame.Rect(
                    region_config['x'],
                    region_config['y'],
                    region_config['width'],
                    region_config['height']
                )

                self.regions.append(ClickRegion(
                    name=region_config['name'],
                    rect=rect,
                    event_type=region_config.get('event', region_config['name'])
                ))

            logger.info(f"Touchscreen custom regions: {len(self.regions)} regions")

    def process_event(self, pygame_event) -> Optional['InputData']:
        """
        Process pygame mouse event

        Args:
            pygame_event: pygame.event object

        Returns:
            InputData or None
        """
        from mnky_bx.ui.input_system import InputData, InputType, InputEvent

        if pygame_event.type != pygame.MOUSEBUTTONDOWN:
            return None

        # Check debounce
        current_time = datetime.now()
        if self.last_click_time:
            elapsed = (current_time - self.last_click_time).total_seconds() * 1000
            if elapsed < self.debounce_ms:
                return None

        self.last_click_time = current_time

        # Get click position
        click_pos = pygame.mouse.get_pos()

        logger.debug(f"Touchscreen click at {click_pos}")

        # Check which region was clicked
        for region in self.regions:
            if region.rect.collidepoint(click_pos):
                event_map = {
                    'left_pressed': InputEvent.LEFT_PRESSED,
                    'right_pressed': InputEvent.RIGHT_PRESSED,
                    'confirm': InputEvent.CONFIRM,
                    'back': InputEvent.BACK,
                }

                event_type = event_map.get(
                    region.event_type,
                    InputEvent.LEFT_PRESSED
                )

                logger.debug(f"Touchscreen region '{region.name}' clicked")

                return InputData(
                    event_type=event_type,
                    input_method=InputType.TOUCHSCREEN,
                    timestamp=current_time,
                    position=click_pos
                )

        logger.debug(f"Click at {click_pos} outside all regions")
        return None
