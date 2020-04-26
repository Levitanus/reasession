--
SECTION = 'REASESSION'

render_midi = {}

-- track: reaper track (reaper.GetSelectedTrack(int project, int idx))
-- fx: int index of render_midi JSFX slot
-- RETURN: Array contains table of midi messages
--     {[1]={qn=float PPQ,msg1=int,msg2=int,msg3=int}}
-- NOTE: JSFX will be deleted
function render_midi.get_midi_from_track(track, fx)
    -- msg(track, fx)
    -- reaper.ShowConsoleMsg('\nget_midi_from_track start = ' .. tostring(os.clock()))
    reaper.TrackFX_SetParam(track, fx, 0, 1)
    -- while (reaper.TrackFX_GetParam(track, fx, 0) > 0) do
    --     reaper.ShowConsoleMsg('.')
    -- end
    reaper.gmem_attach("ReasessionRenderMidi")
    local size = reaper.gmem_read(0)
    -- reaper.ShowConsoleMsg('\nsize = ' .. tostring(size))
    -- msg("size:" .. size)
    local qnOffset = 500000
    local bufPtr = 1000000
    local bufLen = 1500000
    local bufBus = 2000000
    local bufOut = 2500000
    local trackbuf = {}
    if (size == 0) then
        return -1
    end
    for i = 1, size do
        -- reaper.ShowConsoleMsg(string.format('\n%s', i))
        trackbuf[i] = {}
        trackbuf[i]['qn'] = reaper.gmem_read(i + qnOffset - 1)
        trackbuf[i]['bufPtr'] = reaper.gmem_read(i + bufPtr - 1)
        trackbuf[i]['bufLen'] = reaper.gmem_read(i + bufLen - 1)
        trackbuf[i]['bufBus'] = reaper.gmem_read(i + bufBus - 1)
        -- reaper.ShowConsoleMsg(string.format('\n----qn:%s, ptr:%s, len:%s, bus:%s', trackbuf[i]['qn'],trackbuf[i]['bufPtr'],trackbuf[i]['bufLen'],trackbuf[i]['bufBus']))
        trackbuf[i]['bufOut'] = {}
        -- reaper.ShowConsoleMsg('\n----bufout:')
        for i2 = 1, trackbuf[i]['bufLen'] do
            trackbuf[i]['bufOut'][i2] =
            reaper.gmem_read(bufOut + (trackbuf[i]['bufPtr'] + (i2 - 1)))
            -- reaper.ShowConsoleMsg(string.format('\n--------%s', trackbuf[i]['bufOut'][i2]))
        end
        reaper.TrackFX_Delete(track, fx)
    end
    -- reaper.ShowConsoleMsg('\nget_midi_from_track end = ' .. tostring(os.clock()))
    return trackbuf
end

-- RETURN: track, fx
--     `track` is Reaper Track object, `fx` is fx index
function render_midi.get_task()
    -- reaper.ShowConsoleMsg('\nget_task start = ' .. tostring(os.clock()))
    fx = tonumber(reaper.GetExtState(SECTION, 'render_midi_fx_idx'))
    trackidx = tonumber(reaper.GetExtState(SECTION, 'render_midi_track_idx'))
    proj = tonumber(reaper.GetExtState(SECTION, 'render_midi_proj_idx'))
    track = reaper.GetTrack(proj, trackidx)
    -- reaper.ShowConsoleMsg('\nget_task end = ' .. tostring(os.clock()))
    return track, fx
end

function get_buf_str(buf)
    local buftbl = {}
    for i, v in ipairs(buf) do
        -- if i > 1 then table.insert(buftbl, ',') end
        table.insert(buftbl, tostring(v))
    end
    return string.format('[%s]', table.concat(buftbl, ','))
end

function render_midi.trackbuf_to_str(trackbuf)
    -- reaper.ShowConsoleMsg('\ntrackbuf_to_str start = ' .. tostring(os.clock()))
    local restbl = {}
    for i, v in ipairs(trackbuf) do
        -- if i > 1 then table.insert(restbl, ',') end
        local qn = v['qn']
        local bus = v['bufBus']
        local buf = get_buf_str(v['bufOut'])
        -- reaper.ShowConsoleMsg('\n'..buf)
        local item = string.format('{"qn":%s, "bus":%s, "buf":%s}', qn, bus, buf)
        -- reaper.ShowConsoleMsg('\n'..item)
        table.insert(restbl, item)
        -- reaper.ShowConsoleMsg('\n'..result_str)
    end
    local result = string.format('[%s]', table.concat(restbl, ','))
    -- reaper.ShowConsoleMsg('\ntrackbuf_to_str end = ' .. tostring(os.clock()))
    -- reaper.ShowConsoleMsg('\nresult:\n--------\n' .. result)
    return result
end

-- reaper.ShowConsoleMsg('running\n')
-- track = reaper.GetTrack(0, 1)
-- fx = 0
-- trackbuf_now = render_midi.get_midi_from_track(track, fx)

track, fx = render_midi.get_task()
trackbuf = render_midi.get_midi_from_track(track, fx)
-- reaper.ShowConsoleMsg('\n' .. render_midi.trackbuf_to_str(trackbuf))
reaper.SetExtState(SECTION,
    'render_midi_output',
    render_midi.trackbuf_to_str(trackbuf),
    false)
