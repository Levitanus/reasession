item =  reaper.GetSelectedMediaItem( 0, 0 )
-- take =  reaper.GetActiveTake( item )
take = reaper.MIDIEditor_GetTake(reaper.MIDIEditor_GetActive())
buf1 = 'mybuf'
retval, buf = reaper.MIDI_GetAllEvts( take, buf1 )
reaper.ShowConsoleMsg('\n'..buf:len()..', '..string.len(buf)..'\n')
reaper.ShowConsoleMsg(buf)
reaper.ShowConsoleMsg(buf1)