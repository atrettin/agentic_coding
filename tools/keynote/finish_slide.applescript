-- usage: osascript finish_slide.applescript <doc> <old index> <old title prefix> <console file|""> <image|""> <x> <y> <w> <h> <notes prefix file|"">
-- Completes the slide that build_slide.applescript appended (the last slide): fills the console box
-- (the shape at x = 960), places an image, prepends a notes prefix to the old slide's presenter notes,
-- then puts the new slide in place of the old one.
on readFile(p)
	return read POSIX file p as «class utf8»
end readFile

on run argv
	set {docName, oldIdx, oldPrefix, consoleFile, imgPath} to items 1 thru 5 of argv
	set {ix, iy, iw, ih, notesFile} to items 6 thru 10 of argv
	set oldIdx to oldIdx as integer
	tell application "Keynote"
		set d to document docName
		set old to slide oldIdx of d
		set oldTitle to object text of default title item of old
		if oldTitle does not start with oldPrefix then error "slide " & oldIdx & " is '" & oldTitle & "', expected '" & oldPrefix & "'"
		set s to last slide of d

		if consoleFile is not "" then
			set done to false
			repeat with x in iWork items of s
				if class of x is shape and (item 1 of (position of x as list)) = 960 then
					set object text of x to my readFile(consoleFile)
					set done to true
				end if
			end repeat
			if not done then error "no console box on new slide"
		end if

		if imgPath is not "" then
			set f to (POSIX file imgPath) as alias
			tell s to make new image with properties {file:f, position:{ix as integer, iy as integer}, width:iw as integer, height:ih as integer}
		end if

		set n to presenter notes of old as text
		if notesFile is not "" then set n to my readFile(notesFile) & linefeed & linefeed & n
		set presenter notes of s to n

		move s to after old
		delete slide oldIdx of d
	end tell
end run
