{ self, inputs, ... }: {

	flake.wrappers.alacritty = { pkgs, wlib, ... }: {
		imports = [ wlib.wrapperModules.alacritty ];
		settings.terminal.shell = {
			program = "${pkgs.fish}/bin/fish";
			args = [ "-l" ];
		};
	};

}
