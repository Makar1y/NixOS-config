{ self, inputs, ... }: {

	flake.wrappers.niri = { pkgs, wlib, ... }: {
		imports = [ wlib.wrapperModules.niri ];
		settings = {
			prefer-no-csd = _: { };
			workspaces = {
				"1" = _: { };
				"2" = _: { };
				"3" = _: { };
				"4" = _: { };
				"5" = _: { };
			};
			input.focus-follows-mouse = _: { };
			input.keyboard.xkb = {
				layout = "us,lt,ru";
				options = "grp:alt_shift_toggle";
			};
			input.touchpad = {
				tap = _: { };
			};
			layout = {
				gaps = 10;
				always-center-single-column = _: { };
				focus-ring = {
					width = 2;
				};
			};
			window-rules = [
				{
					draw-border-with-background = false;
					geometry-corner-radius = 12;
					clip-to-geometry = true;
				}
			];
			cursor = {
				"xcursor-size" = 12;
			};
			gestures.hot-corners = { off = _: { }; }; 
			hotkey-overlay = { skip-at-startup = _: { }; };
			spawn-at-startup = [
				"noctalia-shell"
			];
			binds = import ./_binds.nix;
		};
	};

	flake.nixosModules.niri = { pkgs, lib, ... }: {
		programs.niri = {
			enable = true;
			package = self.packages.${pkgs.stdenv.hostPlatform.system}.niri;
		};
	};
}
