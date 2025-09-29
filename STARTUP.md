# Auto-Start Configuration

The three-models application is configured to start automatically when you log in to macOS.

## Location

The LaunchAgent configuration is installed at:
```
~/Library/LaunchAgents/com.threemodels.startup.plist
```

## Management Commands

### Stop auto-start
```bash
launchctl unload ~/Library/LaunchAgents/com.threemodels.startup.plist
```

### Start auto-start
```bash
launchctl load ~/Library/LaunchAgents/com.threemodels.startup.plist
```

### Remove auto-start completely
```bash
launchctl unload ~/Library/LaunchAgents/com.threemodels.startup.plist
rm ~/Library/LaunchAgents/com.threemodels.startup.plist
```

### Check if it's running
```bash
launchctl list | grep threemodels
```

### View logs
```bash
# Standard output
tail -f /Users/michaelbernaski/Developer/three-models/startup.log

# Error output
tail -f /Users/michaelbernaski/Developer/three-models/startup.error.log
```

## Behavior

- The application will open in a new Terminal window at login
- It runs the streaming Python version (`run_python.sh`)
- You can close the Terminal window to stop the application
- It will restart automatically on next login

## Manual Start

If you disable auto-start, you can still run manually:
```bash
./run_python.sh
```