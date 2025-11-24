# GUIControl - Gesture Control GUI Application

<div align="center">
  <p>
    <a href="README_EN.md">English</a> | 
    <a href="README.md">中文</a>
  </p>
</div>

A Python-based gesture recognition and mouse control application that uses camera to capture gestures for controlling computer mouse operations.

## Features

- **Real-time Gesture Recognition**: High-precision gesture detection using MediaPipe library
- **Mouse Control**: Mouse movement and click operations through gestures
- **Performance Optimization**: Optimized for background operation
- **Error Handling**: Comprehensive error handling and resource management
- **Extensible Architecture**: Modular design for easy addition of new gesture functions

## System Requirements

- Python 3.12+
- Windows operating system
- Camera device

## Installation

Project uses uv as package manager, install dependencies:

```bash
uv sync
```

Or install using pip:

```bash
pip install -e .
```

### Main Dependencies

- `mediapipe>=0.10.21` - Core gesture recognition library
- `opencv-python>=4.11.0.86` - Image processing and camera control
- `pyautogui>=0.9.54` - Mouse and keyboard control
- `pywin32>=311` - Windows system API calls
- `keyboard>=0.13.5` - Keyboard event listening
- `psutil>=7.1.3` - System process management

## Project Structure

```
GUIControl/
├── main.py                 # Main program entry
├── utils/
│   ├── hgr_utils.py        # Gesture recognition utility class
│   └── gui_utils.py        # GUI control utility class
├── data/                   # Data storage directory
│   └── hand_landmarks.npy  # Gesture data file
├── pyproject.toml          # Project configuration and dependencies
├── README.md              # Chinese documentation
└── README_EN.md           # English documentation
```

## Usage

### Launch Application

Run the main program:

```bash
python main.py
```

### Basic Operations

1. The program will automatically open the camera after startup
2. Place your hand in front of the camera for gesture recognition
3. The system will detect gestures in real-time and convert them to mouse operations
4. Press `Ctrl+C` to exit the program

### Gesture Functions

Currently supported gesture functions:

- **Mouse Movement**: When middle finger and thumb touch, use index finger as detection point to control mouse pointer movement
- **Click Operation**: Trigger mouse click when index finger and thumb touch
- **Pause/Resume**: Automatically pause control when hand leaves camera range

## Technical Architecture

### Core Components

1. **GestureControl Class** (`main.py`)
   - Main control class managing the entire gesture control process
   - Responsible for initialization, error handling, performance monitoring

2. **HGRUtils Class** (`utils/hgr_utils.py`)
   - Core gesture recognition functionality
   - MediaPipe-based gesture detection
   - Camera control and image processing

3. **GUIController Class** (`utils/gui_utils.py`)
   - GUI control interface
   - Mouse operation encapsulation

### Performance Optimization

- **Frame Rate Control**: Target 30 FPS for smooth operation
- **Memory Optimization**: Pre-allocated memory and caching mechanisms
- **Background Optimization**: System optimization for background operation
- **Error Recovery**: Automatic error counting and recovery mechanism

## Development Guide

### Adding New Gesture Functions

1. Add new gesture function classes to `function_list` in `main.py`
2. Implement gesture recognition logic
3. Integrate into the main control loop

### Custom Configuration

Adjust system behavior by modifying constants in `main.py`:

```python
# Frame rate settings
TARGET_FPS = 30

# Data directory
DEFAULT_DATA_DIR = "./data"

# Control method
DEFAULT_CONTROL_METHOD = "hardware"

# Error handling
MAX_ERROR_COUNT = 5
```

## Troubleshooting

### Common Issues

1. **Camera cannot open**
   - Check if camera is being used by other programs
   - Ensure camera drivers are working properly

2. **Gesture recognition inaccurate**
   - Ensure adequate lighting
   - Adjust distance between hand and camera
   - Check camera resolution settings

3. **Performance issues**
   - Close unnecessary background programs
   - Reduce camera resolution (adjust in code)

### Debug Mode

The program includes detailed log output to help diagnose problems:

- Startup information
- Error reports
- Performance statistics

## Contributing

Welcome to submit Issues and Pull Requests to improve the project.

### Development Environment Setup

1. Clone the project
2. Install dependencies
3. Run test script: `python test.py`

## License

This project uses MIT License.

## Changelog

### v0.1.0
- Initial version release
- Basic gesture recognition functionality
- Mouse control functionality
- Performance optimization and error handling

## Contact

For questions or suggestions, please submit feedback through the project Issue page.
QQ: 2655998023