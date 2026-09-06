{ self, inputs, ... }: {

	flake.wrappers.niri = { pkgs, wlib, ... }: {
		imports = [ wlib.wrapperModules.niri ];
		settings = {
			input.keyboard.xkb = {
				layout = "us,lt,ru";
				options = "grp:alt_shift_toggle";
			};
			input.touchpad = {
				tap = _: { };
			};
			layout.gaps = 5;
			gestures.hot-corners = { off = _: { }; };
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
