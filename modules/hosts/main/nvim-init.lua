vim.opt.termguicolors = true

local transparent = function(hl)
	vim.api.nvim_set_hl(0, hl, { bg = "NONE" })
end

for _, hl in ipairs {
	"Normal",
	"NormalNC",
	"NormalFloat",
	"FloatBorder",
	"SignColumn",
	"LineNr",
	"CursorLineNr",
	"CursorLine",
	"FoldColumn",
	"EndOfBuffer",
	"Pmenu",
	"PmenuSel",
	"StatusLine",
	"StatusLineNC",
	"TabLine",
	"TabLineFill",
	"TabLineSel",
} do
	transparent(hl)
end