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
function get_script_path()
  local info = debug.getinfo(1,'S')
  local script_path = info.source:match[[^@?(.*[\/])[^\/]-$]]
  return script_path
end
function get_file_separator()
  local OS = reaper.GetOS()
  if OS ~= "Win32" and OS ~= "Win64" then
    return "/"
  end
  return "\\"
end

local script_path = get_script_path() .. get_file_separator()

package.path = package.path .. ";" .. script_path .."?.lua"

require "json"

---------------------------TEST MIDI  DATA--------------------------------------
test_midi = {[1] = {
    [1] = {msg1 = 144.0, qn = 0.99845804988662, msg2 = 47.0, msg3 = 58.0, },
    [2] = {msg1 = 144.0, qn = 1.2366748139603, msg2 = 48.0, msg3 = 75.0, },
    [3] = {msg1 = 128.0, qn = 1.4098473823744, msg2 = 47.0, msg3 = 64.0, },
    [4] = {msg1 = 144.0, qn = 1.4098473823744, msg2 = 50.0, msg3 = 78.0, },
    [5] = {msg1 = 128.0, qn = 1.4747870955296, msg2 = 48.0, msg3 = 64.0, },
    [6] = {msg1 = 144.0, qn = 1.6263130928919, msg2 = 48.0, msg3 = 73.0, },
    [7] = {msg1 = 128.0, qn = 1.6912528060471, msg2 = 50.0, msg3 = 64.0, },
    [8] = {msg1 = 128.0, qn = 1.7345459481506, msg2 = 48.0, msg3 = 64.0, },
    [9] = {msg1 = 176.0, qn = 2.1336252121242, msg2 = 1.0, msg3 = 63.0, },
    [10] = {msg1 = 176.0, qn = 2.1336252121242, msg2 = 1.0, msg3 = 64.0, },
    [11] = {msg1 = 176.0, qn = 2.1336252121242, msg2 = 1.0, msg3 = 65.0, },
    [12] = {msg1 = 144.0, qn = 2.5063009010122, msg2 = 50.0, msg3 = 69.0, },
    [13] = {msg1 = 144.0, qn = 2.6460542843452, msg2 = 48.0, msg3 = 79.0, },
    [14] = {msg1 = 128.0, qn = 2.6926387454562, msg2 = 50.0, msg3 = 64.0, },
    [15] = {msg1 = 144.0, qn = 2.6926387454562, msg2 = 47.0, msg3 = 70.0, },
    [16] = {msg1 = 144.0, qn = 2.8789765899001, msg2 = 50.0, msg3 = 89.0, },
    [17] = {msg1 = 128.0, qn = 2.9488532815666, msg2 = 47.0, msg3 = 64.0, },
    [18] = {msg1 = 128.0, qn = 2.9954377426776, msg2 = 48.0, msg3 = 64.0, },
    [19] = {msg1 = 128.0, qn = 3.1304969896908, msg2 = 50.0, msg3 = 64.0, },
}, }
--------------------------------------------------------------------------------

reaper.ClearConsole()

function bytesToString(bytes)
    local buf = string.rep(' ', #bytes)
    local i = 0
    return (string.gsub(buf, '(.)',
    function(c)i = i + 1
    return string.char(bytes[i])end))
end

function extract_note(idx, trackbuf)
    local mmsg = trackbuf[i]
    local ch = mmsg['msg1'] - 0x90
    local start_qn = mmsg['qn']
    local note = mmsg['msg2']
    local vel = mmsg['msg3']
    local i = idx
    repeat
        if trackbuf[i]['msg1'] - 0x80 == ch and trackbuf[i]['msg2'] == note then
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
end
function filter_notes(trackbuf)
    local evtbuf = {}
    local notebuf = {}
    local mmsg
    local note_evt
    local bmsg
    i = 1
    repeat
        mmsg = trackbuf[i]
        if mmsg['msg1'] >= 0x90 and mmsg['msg1'] < 0xA0 then
            note_evt = extract_note(i, trackbuf)
            table.insert(notebuf, note_evt)
        else
            if mmsg['msg1'] < 0x80 or mmsg['msg1'] > 0x90 then
                bmsg = bytesToString({mmsg['msg1'], mmsg['msg2'], mmsg['msg3']})
                table.insert(evtbuf, {qn = mmsg['qn'], msg = bmsg})
            end
        end
        i = i + 1
    until(trackbuf[i] == nil)
    return notebuf, evtbuf
end

function insert_events(notebuf, evtbuf, take)
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
        endppqpos = reaper.MIDI_GetPPQPosFromProjQN(take,value['end_qn'])
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

function erase_items_on_track(track)
    local num = reaper.CountTrackMediaItems(track)
    if num == 0 then
        return nil
    end
    for i = 1, num do
        item = reaper.GetTrackMediaItem(track, i-1)
        reaper.DeleteTrackMediaItem(track, item)
    end
end

function midibuf_to_track(project, track, track_midi_buf)
    erase_items_on_track(track)
    local pr_length = reaper.GetProjectLength(project)
    local item = reaper.CreateNewMIDIItemInProj(track, project, pr_length, false)
    local take = reaper.GetMediaItemTake(item, 0)
    local notebuf
    local evtbuf
    notebuf, evtbuf = filter_notes(track_midi_buf)
    insert_events(notebuf, evtbuf, take)
end

function midibuf_to_tracks(project, tracks, midi_buf)
    assert(#tracks == #midi_buf, string.format(
        "amount of tracks (%s) not equal to amount of input midi buffers (%s)",
        #tracks, #midi_buf))
    for i,track in ipairs(tracks) do
        midibuf_to_track(project, track, midi_buf[i])
    end
end

function get_tracks_by_idx(project, ...)
    local idxs = {...}
    local tracks = {}
    for i,v in ipairs(idxs) do
        tracks[i] =  reaper.GetTrack(project, v)
    end
    return tracks
end

tracks = get_tracks_by_idx(0, 4,5)
midibuf_to_tracks(0, tracks, test_midi)
