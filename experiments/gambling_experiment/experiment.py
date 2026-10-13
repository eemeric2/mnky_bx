# experiments/gambling_experiment/experiment.py (EXAMPLE)

from mnky_bx.core.experiment_base import ExperimentBase
import pygame

class GamblingExperiment(ExperimentBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Experiment-specific setup
    
    def wait_for_response(self):
        """Wait for button response"""
        running = True
        start_time = pygame.time.get_ticks()
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    return False
            
            # Check for button press (from Arduino callback)
            if self.choice in ['left', 'right']:
                return True
            
            # Check timeout
            if pygame.time.get_ticks() - start_time > self.max_RT:
                self.choice = 'no response'
                return False
            
            pygame.time.delay(4)
        
        return True