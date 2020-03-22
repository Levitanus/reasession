----------------------------------DESCRIPTION-----------------------------------
-- Module provides functions for full-speed render of midi.

-- EXAMPLE OF USAGE:
--
-- project = 0
-- tracks_in = render_midi.get_tracks_by_idx(project, 0,1,2,3)
-- tracks_out = render_midi.get_tracks_by_idx(project, 4,5,6,7)
-- midibuf = render_midi.render(project, tracks_in)
-- render_midi.midibuf_to_tracks(project, tracks_out, midibuf, nil)

-- MAIN FUNCTIONS:

-- -- Main render function.
-- --     adds JSFX to tracks, renders, gets midi from them
-- --     and removes JSFX and unnecessary files
-- -- project: int reaper project
-- -- tracks Array of reaper tracks
-- -- RETURN: Array of track messages Arrays
-- --     {
-- --         [1]={[1]={qn=float PPQ,msg1=int,msg2=int,msg3=int}, ...}
-- --         [2]={[1]={qn=float PPQ,msg1=int,msg2=int,msg3=int}, ...}
-- --     }
-- function render_midi.render(project, tracks)

-- -- project: int
-- -- tracks: Array of ReaperTrack
-- -- midi_buf: Array of note_events_buf {
-- --      [1]={[1]={start_qn=float,end_qn=float,ch=int,note=int,vel=int},...},
-- --      [2]={[1]={start_qn=float,end_qn=float,ch=int,note=int,vel=int},...},
-- --      ...}
-- -- length: number items length or nil for usage of project length
-- -- NO RETURN
-- function render_midi.midibuf_to_tracks(project, tracks, midi_buf, length)

-- -- project: int
-- -- track: ReaperTrack
-- -- track_midi_buf: Array of note_events_buf
-- --      {[1]={start_qn=float,end_qn=float,ch=int,note=int,vel=int},...}
-- -- length: number items length or nil for usage of project length
-- -- NO RETURN
-- function render_midi.midibuf_to_track(project, track, track_midi_buf, length)

-- HELPER FUNCTIONS:

-- -- project: int reaper project
-- -- RETURN: Array of selected reaper tracks
-- function render_midi.get_selected_tracks(project)

-- -- project: int reaper project
-- -- int indexed separated by comma
-- --     render_midi.get_tracks_by_idx(project, 1, 2, 3)
-- -- RETURN: Array of reaper tracks
-- function render_midi.get_tracks_by_idx(project, ...)

-- -- tracks: Array of reaper tracks
-- -- NO RETURN
-- function render_midi.set_selection_to_tracks(tracks)

---------------------------SERVICE FUNCTIONS------------------------------------
local function msg(...)
    local args = {...}
    local message = ''
    for i, v in ipairs(args) do
        if i > 1 then
            message = message .. ', '
        end
        message = message .. tostring(v)
    end
    reaper.ShowConsoleMsg(message .. "\n")
end
--------------------------------------------------------------------------------

render_midi = {}

-- track: reaper track (reaper.GetSelectedTrack(int project, int idx))
-- RETURN: int fx index on track
function render_midi.add_jsfx_to_track(track)
    local JSFX_NAME = 'render_midi'
    local fx = reaper.TrackFX_AddByName(track, JSFX_NAME, false, 1)
    return fx
end

-- tracks: Array of reaper tracks
-- RETURN: Array of tables {[1]={track=track,fx=fx_index},...}
function render_midi.add_jsfx_to_tracks(tracks)
    local tracks_w_fx = {}
    for i, track in ipairs(tracks) do
        tracks_w_fx[i] = {}
        tracks_w_fx[i]['track'] = track
        tracks_w_fx[i]['fx'] = render_midi.add_jsfx_to_track(track)
    end
    return tracks_w_fx
end

-- track: reaper track (reaper.GetSelectedTrack(int project, int idx))
-- fx: int index of render_midi JSFX slot
-- RETURN: Array contains table of midi messages
--     {[1]={qn=float PPQ,msg1=int,msg2=int,msg3=int}}
-- NOTE: JSFX will be deleted
function render_midi.get_midi_from_track(track, fx)
    -- msg(track, fx)
    reaper.TrackFX_SetParam(track, fx, 0, 1)
    reaper.gmem_attach("RenderMidiNameSpace")
    local size = reaper.gmem_read(0)
    -- msg("size:" .. size)
    local qnOffset = 1;
    local msg1Offset = 1000000
    local msg2Offset = 2000000
    local msg3Offset = 3000000
    local trackbuf = {}
    if (size == 0) then
        return - 1
    end
    for i = 1, size do
        trackbuf[i] = {}
        trackbuf[i]['qn'] = reaper.gmem_read(i + qnOffset - 1)
        trackbuf[i]['msg1'] = reaper.gmem_read(i + msg1Offset - 1)
        trackbuf[i]['msg2'] = reaper.gmem_read(i + msg2Offset - 1)
        trackbuf[i]['msg3'] = reaper.gmem_read(i + msg3Offset - 1)
    end
    reaper.TrackFX_Delete(track, fx)
    return trackbuf
end

-- tracks_w_fx: Array of tables {[1]={track=track,fx=fx_index},...}
-- RETURN: Array of track messages Arrays
--     {
--         [1]={[1]={qn=float PPQ,msg1=int,msg2=int,msg3=int}, ...}
--         [2]={[1]={qn=float PPQ,msg1=int,msg2=int,msg3=int}, ...}
--     }
-- NOTE: JSFX 'render_midi' on tracks will be deleted
function render_midi.get_midi_from_tracks(tracks_w_fx)
    local outBuf = {}
    local trackbuf
    for i, track in ipairs(tracks_w_fx) do
        -- msg(i, track['track'], track['fx'])
        trackbuf = render_midi.get_midi_from_track(track['track'],
        track['fx'])
        outBuf[i] = trackbuf
        -- msg(serdes.tableToString(trackbuf))
    end
    return outBuf
end

-- project: int
-- settings_int: Array of tables, made from reaper.GetSetProjectInfo
--    {{'RENDER_SETTINGS', 0},
--     {'RENDER_BOUNDSFLAG', 0}, ...}
-- settings_str: Array of tables, made from reaper.GetSetProjectInfo_String
--    {{'RENDER_FILE', ''},
--     {'RENDER_PATTERN', 'myfile'}, ...}
-- NO RETURN!!! TABLES WILL BE MODIFYED
function render_midi.get_render_settings(project, settings_int, setings_str)
    for i, v in ipairs(settings_int) do
        v[2] = reaper.GetSetProjectInfo(project, v[1], 0, false)
        -- msg(v[1], v[2])
    end
    for i, v in ipairs(setings_str) do
        retval, v[2] = reaper.GetSetProjectInfo_String(project, v[1], v[2], false)
        -- msg(v[1], v[2])
    end
end

-- project: int
-- settings_int: Array of tables, made from reaper.GetSetProjectInfo
--    {{'RENDER_SETTINGS', 0},
--     {'RENDER_BOUNDSFLAG', 0}, ...}
-- settings_str: Array of tables, made from reaper.GetSetProjectInfo_String
--    {{'RENDER_FILE', ''},
--     {'RENDER_PATTERN', 'myfile'}, ...}
-- NO RETURN
function render_midi.set_render_settings(project, settings_int, setings_str)
    for i, v in ipairs(settings_int) do
        reaper.GetSetProjectInfo(project, v[1], v[2], true)
    end
    for i, v in ipairs(setings_str) do
        reaper.GetSetProjectInfo_String(project, v[1], v[2], true)
    end
end

-- path: string content of RENDER_FILE option
-- pattern: string content of RENDER_PATTERN option
-- tracks: any iterable, representing amount of rendered tracks
-- NO RETURN
-- NOTE: use with care, function physically removes files
function render_midi.remove_rendered_audio(path, pattern, tracks)
    local filename = ''
    local num = ''
    local sep = '/'
    local retval = false
    if reaper.GetOS() == 'Win32' or reaper.GetOS() == 'Win64' then sep = '\\' end
    filename = path .. sep .. pattern .. '.ogg'
    retval = os.remove(filename)
    for i,v in ipairs(tracks) do
        num = tostring(i)
        if string.len(num) < 3 then
            num = string.rep('0', 3-string.len(num)) .. num
        end
        filename = path .. sep .. pattern .. "-" .. num .. '.ogg'
        retval = os.remove(filename)
        -- msg('return of os.remove of ',filename,':',retval)
    end
end

-- project: int reaper project
-- RETURN: Array of selected reaper tracks
function render_midi.get_selected_tracks(project)
    local num = reaper.CountSelectedTracks(0)
    local tracks = {}
    for i = 1, num do
        tracks[i] = reaper.GetSelectedTrack(project, i - 1)
    end
    return tracks
end

-- project: int reaper project
-- int indexed separated by comma
--     render_midi.get_tracks_by_idx(project, 1, 2, 3)
-- RETURN: Array of reaper tracks
function render_midi.get_tracks_by_idx(project, ...)
    local idxs = {...}
    local tracks = {}
    for i,v in ipairs(idxs) do
        tracks[i] =  reaper.GetTrack(project, v)
    end
    return tracks
end

-- tracks: Array of reaper tracks
-- NO RETURN
function render_midi.set_selection_to_tracks(tracks)
    for i,track in ipairs(tracks) do
        if i == 1 then
            reaper.SetOnlyTrackSelected(track)
        else
            reaper.SetTrackSelected(track, true)
        end
    end
end

-- Perform quick render with removal of resulted files
-- project: int reaper project
-- tracks: Array of reaper tracks to render
-- NO RETURN
function render_midi.render_action(project, tracks)
    -- render_action: Render project, using the most recent
    --     render settings, auto-close render dialog
    local render_action = 42230
    local resource_path = reaper.GetResourcePath()
    local pattern = 'temp_for_render_midi'
    local original_settings_int = {
        {'RENDER_SETTINGS', 0},
        {'RENDER_BOUNDSFLAG', 0},
        {'RENDER_CHANNELS', 0},
        {'RENDER_SRATE', 0},
        {'RENDER_STARTPOS', 0},
        {'RENDER_ENDPOS', 0},
        {'RENDER_TAILFLAG', 0},
        {'RENDER_TAILMS', 0},
        {'RENDER_ADDTOPROJ', 0},
        {'RENDER_DITHER', 0},
    }
    local original_settings_str = {
        {'RENDER_FILE', ''},
        {'RENDER_PATTERN', ''},
        {'RENDER_FORMAT', ''},
    }
    local new_settings_int = {
        {'RENDER_SETTINGS', 3.0},
        {'RENDER_BOUNDSFLAG', 1},
        {'RENDER_CHANNELS', 1},
        {'RENDER_ADDTOPROJ', 0},
        {'RENDER_SRATE', 0},
    }
    local new_settings_str = {
        {'RENDER_FILE', resource_path},
        {'RENDER_PATTERN', pattern},
        {'RENDER_FORMAT', 'vggo'},
    }
    local selected_tracks = render_midi.get_selected_tracks(project)
    render_midi.set_selection_to_tracks(tracks)
    render_midi.get_render_settings(project, original_settings_int,
        original_settings_str)
    render_midi.set_render_settings(project, new_settings_int, new_settings_str)
    reaper.Main_OnCommandEx(render_action, 0, project)
    -- get_render_settings(project, new_settings_int, new_settings_str)
    render_midi.set_render_settings(project, original_settings_int,
        original_settings_str)
    render_midi.remove_rendered_audio(resource_path, pattern, tracks)
    render_midi.set_selection_to_tracks(selected_tracks)
end

-- Main render function.
--     adds JSFX to tracks, renders, gets midi from them
--     and removes JSFX and unnecessary files
-- project: int reaper project
-- tracks Array of reaper tracks
-- RETURN: Array of track messages Arrays
--     {
--         [1]={[1]={qn=float PPQ,msg1=int,msg2=int,msg3=int}, ...}
--         [2]={[1]={qn=float PPQ,msg1=int,msg2=int,msg3=int}, ...}
--     }
function render_midi.render(project, tracks)
    local tracks_w_fx = render_midi.add_jsfx_to_tracks(tracks)
    render_midi.render_action(project, tracks)
    local tracks_midi = render_midi.get_midi_from_tracks(tracks_w_fx)
    return tracks_midi
end

-- bytes: {int msg1, int msg2, int msg3}
-- RETURN: string for using in reaper.MIDI_InsertEvt
function render_midi.bytesToString(bytes)
    local buf = string.rep(' ', #bytes)
    local i = 0
    return (string.gsub(buf, '(.)',
    function(c)i = i + 1
    return string.char(bytes[i])end))
end

-- idx: int index of note_on event in trackbuf
-- trackbuf: Array of track messages Arrays
--     {[1]={qn=float PPQ,msg1=int,msg2=int,msg3=int}, ...}
-- RETURN: {start_qn=float,end_qn=float,ch=int,note=int,vel=int}
function render_midi.extract_note(idx, trackbuf)
    local mmsg = trackbuf[i]
    local ch = mmsg['msg1'] - 0x90
    local start_qn = mmsg['qn']
    local note = mmsg['msg2']
    local vel = mmsg['msg3']
    local i = idx
    repeat
        if trackbuf[i]['msg1'] - 0x80 == ch and trackbuf[i]['msg2'] == note or
            trackbuf[i]['msg1'] - 0x90 == ch and trackbuf[i]['msg2'] == note and
            trackbuf[i]['msg3'] == 0 then
            end_qn = trackbuf[i]['qn']
            return {
                start_qn = start_qn,
                end_qn = end_qn,
                ch = ch,
                note = note,
                vel = vel}
        end
        i = i + 1
    until(trackbuf[i] == nil)
    -- msg('no note off for', note,'at', start_qn)
    return {
            start_qn = start_qn,
            end_qn = nil,
            ch = ch,
            note = note,
            vel = vel}
end

-- trackbuf: Array of track messages Arrays
--     {[1]={qn=float,msg1=int,msg2=int,msg3=int}, ...}
-- RETURN: {
--     Array of note_events_buf {
--         [1]={start_qn=float,end_qn=float,ch=int,note=int,vel=int},...},
--     Array of other events buf{
--         [1]={qn=float, msg=bytestr for using in reaper.MIDI_InsertEvt},...}
-- }
function render_midi.filter_notes(trackbuf)
    local evtbuf = {}
    local notebuf = {}
    local mmsg
    local note_evt
    local bmsg
    i = 1
    repeat
        mmsg = trackbuf[i]
        if mmsg['msg1'] >= 0x90 and mmsg['msg1'] < 0xA0 then
            note_evt = render_midi.extract_note(i, trackbuf)
            -- msg(note_evt['note'])
            table.insert(notebuf, note_evt)
        else
            if mmsg['msg1'] < 0x80 or mmsg['msg1'] > 0x90 then
                bmsg = render_midi.bytesToString({mmsg['msg1'],
                    mmsg['msg2'], mmsg['msg3']})
                table.insert(evtbuf, {qn = mmsg['qn'], msg = bmsg})
            end
        end
        i = i + 1
    until(trackbuf[i] == nil)
    return notebuf, evtbuf
end

-- notebuf: Array of note_events_buf {
--     [1]={start_qn=float,end_qn=float,ch=int,note=int,vel=int},...}},
-- evtbuf: Array of other events buf{
--     [1]={qn=float, msg=bytestr for using in reaper.MIDI_InsertEvt},...}}
-- take: ReaperTake
-- length: int maximum length of item
-- NO RETURN
function render_midi.insert_events(notebuf, evtbuf, take, length)
    local ppq
    local qn
    local mmsg
    local startppqpos
    local endppqpos
    local chan
    local pitch
    local vel
    for i,value in ipairs(evtbuf) do
        qn = value['qn']
        mmsg = value['msg']
        ppq = reaper.MIDI_GetPPQPosFromProjQN(take, qn)
        reaper.MIDI_InsertEvt(take, false, false, ppq, mmsg)
    end
    for i,value in ipairs(notebuf) do
        startppqpos = reaper.MIDI_GetPPQPosFromProjQN(take,value['start_qn'])
        if value['end_qn']==nil then
            value['end_qn']= reaper.TimeMap_timeToQN(length) - 0.0001
            -- msg('set note end to', value['end_qn'])
        else
            -- msg('normal note end at', value['end_qn'])
        end
        endppqpos = reaper.MIDI_GetPPQPosFromProjQN(take,value['end_qn'])
        -- msg(startppqpos, endppqpos)
        chan = value['ch']
        pitch = value['note']
        vel = value['vel']
        reaper.MIDI_InsertNote(
                            take,
                            false,
                            false,
                            startppqpos,
                            endppqpos,
                            chan,
                            pitch,
                            vel,
                            false)
    end
    reaper.MIDI_Sort(take)
end

-- track: ReaperTrack
-- NO RETURN
function render_midi.erase_items_on_track(track)
    local num = reaper.CountTrackMediaItems(track)
    if num == 0 then
        return nil
    end
    for i = 1, num do
        item = reaper.GetTrackMediaItem(track, i-1)
        reaper.DeleteTrackMediaItem(track, item)
    end
end

-- project: int
-- track: ReaperTrack
-- track_midi_buf: Array of note_events_buf
--      {[1]={start_qn=float,end_qn=float,ch=int,note=int,vel=int},...}
-- length: number items length or nil for usage of project length
-- NO RETURN
function render_midi.midibuf_to_track(project, track, track_midi_buf, length)
    render_midi.erase_items_on_track(track)
    local item_length
    if length ~= nil then
        item_length = length
    else
        item_length = reaper.GetProjectLength(project)
    end
    local item = reaper.CreateNewMIDIItemInProj(track,
        project, item_length, false)
    -- msg('item_length calc:',item_length,
    --     'item_length real:',  reaper.GetMediaItemInfo_Value(item, 'D_LENGTH'))
    local take = reaper.GetMediaItemTake(item, 0)
    local notebuf
    local evtbuf
    notebuf, evtbuf = render_midi.filter_notes(track_midi_buf)
    render_midi.insert_events(notebuf, evtbuf, take, item_length)
end

-- project: int
-- tracks: Array of ReaperTrack
-- midi_buf: Array of note_events_buf {
--      [1]={[1]={start_qn=float,end_qn=float,ch=int,note=int,vel=int},...},
--      [2]={[1]={start_qn=float,end_qn=float,ch=int,note=int,vel=int},...},
--      ...}
-- length: number items length or nil for usage of project length
-- NO RETURN
function render_midi.midibuf_to_tracks(project, tracks, midi_buf, length)
    assert(#tracks == #midi_buf, string.format(
        "amount of tracks (%s) not equal to amount of input midi buffers (%s)",
        #tracks, #midi_buf))
    for i,track in ipairs(tracks) do
        render_midi.midibuf_to_track(project, track, midi_buf[i], length)
    end
end


project = 0
tracks_in = render_midi.get_tracks_by_idx(project, 0,1,2,3)
tracks_out = render_midi.get_tracks_by_idx(project, 4,5,6,7)
midibuf = render_midi.render(project, tracks_in)
render_midi.midibuf_to_tracks(project, tracks_out, midibuf, nil)