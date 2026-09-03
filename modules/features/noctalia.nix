{ self, inputs, ...}: {

	flake.wrappers.noctalia-shell = { pkgs, wlib, ... }: {
		imports = [ wlib.wrapperModules.noctalia-shell ];
		settings = (builtins.fromJSON(builtins.readFile ./noctalia.json)).settings;
	};

}
