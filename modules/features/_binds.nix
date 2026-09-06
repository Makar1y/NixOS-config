{
	"Mod+Shift+Slash".show-hotkey-overlay = _: { };

	"Mod+Space".spawn-sh = "noctalia-shell ipc call launcher toggle";
	"Mod+T".spawn = "alacritty";
	# "Mod+D".spawn = "fuzzel";
	"Mod+S".spawn-sh = "noctalia-shell ipc call settings toggle";
	"Mod+O".toggle-overview = _: { repeat = false; };
	"Mod+Q".close-window = _: { repeat = false; };

	"Mod+Left".focus-column-or-monitor-left = _: { };
	"Mod+Down".focus-window-down = _: { };
	"Mod+Up".focus-window-up = _: { };
	"Mod+Right".focus-column-or-monitor-right = _: { };
	"Mod+H".focus-column-or-monitor-left = _: { };
	"Mod+J".focus-window-down = _: { };
	"Mod+K".focus-window-up = _: { };
	"Mod+L".focus-column-or-monitor-right = _: { };

	"Mod+Ctrl+Left".move-column-left = _: { };
	"Mod+Ctrl+Down".move-window-down = _: { };
	"Mod+Ctrl+Up".move-window-up = _: { };
	"Mod+Ctrl+Right".move-column-right = _: { };
	"Mod+Ctrl+H".move-column-left = _: { };
	"Mod+Ctrl+J".move-window-down = _: { };
	"Mod+Ctrl+K".move-window-up = _: { };
	"Mod+Ctrl+L".move-column-right = _: { };

	"Mod+Home".focus-column-first = _: { };
	"Mod+End".focus-column-last = _: { };
	"Mod+Ctrl+Home".move-column-to-first = _: { };
	"Mod+Ctrl+End".move-column-to-last = _: { };

	"Mod+Shift+Left".focus-monitor-left = _: { };
	"Mod+Shift+Down".focus-monitor-down = _: { };
	"Mod+Shift+Up".focus-monitor-up = _: { };
	"Mod+Shift+Right".focus-monitor-right = _: { };
	"Mod+Shift+H".focus-monitor-left = _: { };
	"Mod+Shift+J".focus-monitor-down = _: { };
	"Mod+Shift+K".focus-monitor-up = _: { };
	"Mod+Shift+L".focus-monitor-right = _: { };

	"Mod+Ctrl+Shift+Left".move-column-to-monitor-left = _: { };
	"Mod+Ctrl+Shift+Down".move-column-to-monitor-down = _: { };
	"Mod+Ctrl+Shift+Up".move-column-to-monitor-up = _: { };
	"Mod+Ctrl+Shift+Right".move-column-to-monitor-right = _: { };
	"Mod+Ctrl+Shift+H".move-column-to-monitor-left = _: { };
	"Mod+Ctrl+Shift+J".move-column-to-monitor-down = _: { };
	"Mod+Ctrl+Shift+K".move-column-to-monitor-up = _: { };
	"Mod+Ctrl+Shift+L".move-column-to-monitor-right = _: { };

	"Mod+Page_Down".focus-workspace-down = _: { };
	"Mod+Page_Up".focus-workspace-up = _: { };
	"Mod+I".focus-workspace-down = _: { };
	"Mod+U".focus-workspace-up = _: { };
	"Mod+Ctrl+Page_Down".move-column-to-workspace-down = _: { };
	"Mod+Ctrl+Page_Up".move-column-to-workspace-up = _: { };
	"Mod+Ctrl+U".move-column-to-workspace-down = _: { };
	"Mod+Ctrl+I".move-column-to-workspace-up = _: { };

	"Mod+Shift+Page_Down".move-workspace-down = _: { };
	"Mod+Shift+Page_Up".move-workspace-up = _: { };
	"Mod+Shift+U".move-workspace-down = _: { };
	"Mod+Shift+I".move-workspace-up = _: { };

	"Mod+WheelScrollDown" = _: { props.cooldown-ms = 150; content.focus-workspace-down = _: { }; };
	"Mod+WheelScrollUp" = _: { props.cooldown-ms = 150; content.focus-workspace-up = _: { }; };
	"Mod+Ctrl+WheelScrollDown" = _: { props.cooldown-ms = 150; content.move-column-to-workspace-down = _: { }; };
	"Mod+Ctrl+WheelScrollUp" = _: { props.cooldown-ms = 150; content.move-column-to-workspace-up = _: { }; };
	"Mod+WheelScrollRight".focus-column-right = _: { };
	"Mod+WheelScrollLeft".focus-column-left = _: { };
	"Mod+Ctrl+WheelScrollRight".move-column-right = _: { };
	"Mod+Ctrl+WheelScrollLeft".move-column-left = _: { };
	"Mod+Shift+WheelScrollDown".focus-column-right = _: { };
	"Mod+Shift+WheelScrollUp".focus-column-left = _: { };
	"Mod+Ctrl+Shift+WheelScrollDown".move-column-right = _: { };
	"Mod+Ctrl+Shift+WheelScrollUp".move-column-left = _: { };

	"Mod+1".focus-workspace = 1;
	"Mod+2".focus-workspace = 2;
	"Mod+3".focus-workspace = 3;
	"Mod+4".focus-workspace = 4;
	"Mod+5".focus-workspace = 5;
	"Mod+6".focus-workspace = 6;
	"Mod+7".focus-workspace = 7;
	"Mod+8".focus-workspace = 8;
	"Mod+9".focus-workspace = 9;
	"Mod+Ctrl+1".move-column-to-workspace = 1;
	"Mod+Ctrl+2".move-column-to-workspace = 2;
	"Mod+Ctrl+3".move-column-to-workspace = 3;
	"Mod+Ctrl+4".move-column-to-workspace = 4;
	"Mod+Ctrl+5".move-column-to-workspace = 5;
	"Mod+Ctrl+6".move-column-to-workspace = 6;
	"Mod+Ctrl+7".move-column-to-workspace = 7;
	"Mod+Ctrl+8".move-column-to-workspace = 8;
	"Mod+Ctrl+9".move-column-to-workspace = 9;

	"Mod+BracketLeft".consume-or-expel-window-left = _: { };
	"Mod+BracketRight".consume-or-expel-window-right = _: { };
	"Mod+Comma".consume-window-into-column = _: { };
	"Mod+Period".expel-window-from-column = _: { };

	"Mod+R".switch-preset-column-width = _: { };
	"Mod+Shift+R".switch-preset-column-width-back = _: { };
	"Mod+Ctrl+Shift+R".switch-preset-window-height = _: { };
	"Mod+Ctrl+R".reset-window-height = _: { };

	"Mod+F".maximize-column = _: { };
	"Mod+Shift+F".fullscreen-window = _: { };
	"Mod+M".maximize-window-to-edges = _: { };
	"Mod+Ctrl+F".expand-column-to-available-width = _: { };
	"Mod+C".center-column = _: { };
	"Mod+Ctrl+C".center-visible-columns = _: { };

	"Mod+Minus".set-column-width = "-10%";
	"Mod+Equal".set-column-width = "+10%";
	"Mod+Shift+Minus".set-window-height = "-10%";
	"Mod+Shift+Equal".set-window-height = "+10%";

	"Mod+V".toggle-window-floating = _: { };
	"Mod+Shift+V".switch-focus-between-floating-and-tiling = _: { };
	"Mod+W".toggle-column-tabbed-display = _: { };

	"Print".screenshot = _: { };
	"Ctrl+Print".screenshot-screen = _: { };
	"Alt+Print".screenshot-window = _: { };

	"XF86AudioRaiseVolume".spawn-sh = "noctalia-shell ipc call volume increase";
	"XF86AudioLowerVolume".spawn-sh = "noctalia-shell ipc call volume decrease";
	"XF86AudioMute".spawn-sh = "noctalia-shell ipc call volume muteOutput";
	"XF86MonBrightnessUp".spawn-sh = "noctalia-shell ipc call brightness increase";
	"XF86MonBrightnessDown".spawn-sh = "noctalia-shell ipc call brightness decrease";

	"Mod+Escape" = _: { props.allow-inhibiting = false; content.toggle-keyboard-shortcuts-inhibit = _: { }; };
	"Mod+Shift+E".quit = _: { };
	"Ctrl+Alt+Delete".quit = _: { };
	"Mod+Shift+P".power-off-monitors = _: { };
}