reaper.Undo_BeginBlock()
reaper.ShowConsoleMsg('msg')
reaper.SetProjExtState(0, 'extname', 'key', 'value')
-- reaper.SetExtState('section', 'key', 1, false)
tr = reaper.GetTrack(0, 0)
reaper.AddMediaItemToTrack(tr)
reaper.Undo_EndBlock('test', -1)