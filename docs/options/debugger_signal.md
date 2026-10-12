Default: 0
Example: 1
Type: boolean

Enable external, programmatic activation of the built-in (console) debugger.

When this option is enabled, sending `SIGUSR1` to the FS-UAE process makes it
enter the debugger, exactly as if the debugger hot key (Mod+D / F12+D) had been
pressed. This lets a launcher or wrapper start the debugger without synthesising
a key press.

The signal is only handled when this option is enabled; otherwise `SIGUSR1`
keeps its default behaviour. As with the hot key, the `console_debugger` option
must also be enabled for the debugger to actually be entered.

This is a POSIX feature (Linux, macOS); it is not available on Windows. See
[Debugging](../debugging.md) for examples.
