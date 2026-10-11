{ self, inputs, ...}: {

	# Overlay the wrapper pkgs so noctalia-qs's breakpad build dep builds under
	# gcc 15/16, which otherwise fails to link with:
	#   undefined reference to vtable for google_breakpad::FastSourceLineResolver::Module
	# (wrapper's perSystem pkgs are separate from the host's nixpkgs.overlays).
	perSystem = { pkgs, ... }: {
		wrappers.pkgs = pkgs.extend (final: prev: {
			breakpad = prev.breakpad.overrideAttrs (oldAttrs: {
				patches = (oldAttrs.patches or [ ]) ++ [ ./breakpad-module-factory-vtable.patch ];
			});
		});
	};

	flake.wrappers.noctalia-shell = { pkgs, wlib, ... }: {
		imports = [ wlib.wrapperModules.noctalia-shell ];
		settings = (builtins.fromJSON(builtins.readFile ./noctalia.json)).settings;
	};

}
