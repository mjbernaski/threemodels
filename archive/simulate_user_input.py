#!/usr/bin/env python3
import asyncio
import sys
from unittest.mock import patch, MagicMock

# Simulate user interaction that might trigger the metadata error
async def simulate_user_session():
    """Simulate the exact user interaction that triggers metadata error"""

    # Mock the input function to simulate user typing
    user_inputs = [
        "hello",
        "exit",
        "exit",
        "exit",
        "exit"
    ]

    input_iter = iter(user_inputs)

    def mock_input(prompt):
        try:
            next_input = next(input_iter)
            print(f"[SIMULATED INPUT] {prompt}{next_input}")
            return next_input
        except StopIteration:
            print("[SIMULATED INPUT] No more inputs, stopping")
            raise KeyboardInterrupt()

    # Now run the main function with mocked input
    with patch('builtins.input', side_effect=mock_input):
        # Import and run the main function
        try:
            from run import main
            await main()
        except KeyboardInterrupt:
            print("Simulation ended with KeyboardInterrupt (expected)")
        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f"🚨 CAUGHT EXCEPTION: {error_msg}")
            if 'metadata' in error_msg.lower():
                print(f"🚨 METADATA ERROR FOUND: {error_msg}")
                print(f"🚨 TRACEBACK: {traceback.format_exc()}")
            else:
                print(f"Other error: {traceback.format_exc()}")

if __name__ == '__main__':
    asyncio.run(simulate_user_session())