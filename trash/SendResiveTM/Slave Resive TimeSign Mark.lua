--------------------------------------------------------------------------------
local msg = function(M) reaper.ShowConsoleMsg(tostring(M).."\n") end
--------------------------------------------------------------------------------


local Time_Marker_ser = reaper.GetExtState("Orchestral", "SlaveTempoMark")
local master_track = reaper.GetMasterTrack(0)
local env = reaper.GetTrackEnvelopeByName(master_track, "Tempo map")
reaper.SetEnvelopeStateChunk(env, Time_Marker_ser, 0)
reaper.DeleteExtState("Orchestral", "SlaveTempoMark", 0)

-- msg(Time_Marker_ser)
