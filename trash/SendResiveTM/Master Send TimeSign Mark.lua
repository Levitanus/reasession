--------------------------------------------------------------------------------
local msg = function(M) reaper.ShowConsoleMsg(tostring(M).."\n") end
--------------------------------------------------------------------------------

function TempoMarker()
  local master_track = reaper.GetMasterTrack(0)
  local env = reaper.GetTrackEnvelopeByName(master_track, "Tempo map")
  local retval, tempomap_chunk = reaper.GetEnvelopeStateChunk(env, "", false)

  return tempomap_chunk
end

local TimeSignMarker = TempoMarker()

reaper.SetExtState( "Orchestral", "MasterTempoMark", TimeSignMarker, false) -- ставим флаг запуска EEL_TCP_Master_Server

-- msg(TimeSignMarker)
