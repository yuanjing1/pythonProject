' Starts the Tesla driving alert watcher with no console window.
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = "C:\pythonProject\tesla"
sh.Run """C:\pythonProject\.venv\Scripts\pythonw.exe"" ""C:\pythonProject\tesla\tesla_alert.py""", 0
