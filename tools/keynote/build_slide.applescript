-- usage: osascript build_slide.applescript <doc name> <seed slide index> <title> <body file>
-- body file: one line per paragraph, "level|text" with level 0, 1 or 2.
-- Seed body paragraphs must cycle levels 0,1,2,0,1,2,...  Prints the index of the new slide.
on run argv
	set docName to item 1 of argv
	set seedIdx to (item 2 of argv) as integer
	set theTitle to item 3 of argv
	set bodyLines to paragraphs of (read POSIX file (item 4 of argv) as «class utf8»)

	-- group consecutive equal levels into runs: {level, text}
	set runs to {}
	repeat with ln in bodyLines
		set ln to ln as text
		if ln is not "" then
			set lvl to (character 1 of ln) as integer
			set txt to text 3 thru -1 of ln
			if runs is not {} and (item 1 of last item of runs) = lvl then
				set item 2 of last item of runs to (item 2 of last item of runs) & linefeed & txt
			else
				set end of runs to {lvl, txt}
			end if
		end if
	end repeat

	tell application "Keynote"
		set d to document docName
		duplicate slide seedIdx of d to end of slides of d
		set s to last slide of d
		set skipped of s to false
		set object text of default title item of s to theTitle
		set t to default body item of s
		set n to count paragraphs of object text of t

		-- greedy mapping: seed paragraph j has level (j-1) mod 3
		set keep to {}
		repeat n times
			set end of keep to missing value
		end repeat
		set j to 1
		repeat with r in runs
			repeat while j ≤ n and ((j - 1) mod 3) ≠ (item 1 of r)
				set j to j + 1
			end repeat
			if j > n then error "seed has too few paragraphs for " & (count runs) & " runs"
			set item j of keep to item 2 of r
			set j to j + 1
		end repeat

		-- fill/delete from the end so lower indices stay valid
		repeat with j from n to 1 by -1
			if item j of keep is missing value then
				delete paragraph j of object text of t
			else
				set paragraph j of object text of t to item j of keep
			end if
		end repeat
		return count slides of d
	end tell
end run
