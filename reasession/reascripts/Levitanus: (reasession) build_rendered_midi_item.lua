
-- bytes: {int msg1, int msg2, int msg3}
-- RETURN: string for using in reaper.MIDI_InsertEvt
local function bytesToString(bytes)
    local buf = string.rep(' ', #bytes)
    local i = 0
    return (string.gsub(buf, '(.)',
        function(c)i = i + 1
        return string.char(bytes[i])end))
end

local function extStrToBytes(ext)
    local result = string.gsub(ext, "0xb7c2bc0", '')
    local length = string.len(result)
    reaper.ShowConsoleMsg(tostring(length)..'\n')
    return string.sub(result, 2)
end

-- reaper.ClearConsole()
take_guid = reaper.GetExtState('REASESSION', 'build_midi_on_track_take')
take = reaper.GetMediaItemTakeByGUID(0, take_guid)
events_string = reaper.GetExtState('REASESSION', 'build_midi_on_track_evts')
-- reaper.ShowConsoleMsg(take_guid .. ' : ' .. tostring(take))
-- midiBuf = reaper.GetExtState('REASESSION', 'build_midi_on_track_buf')
-- ppqpos = reaper.GetExtState('REASESSION', 'build_midi_on_track_ppq')

-- reaper.ShowConsoleMsg(midiBuf..'\n')
-- reaper.ShowConsoleMsg(ppqpos..'\n')
-- reaper.ShowConsoleMsg(extStrToBytes(midiBuf))

-- teststring="{[1]={['ppq']=1920.0, ['buf']={[1]=0xb0, [2]=0x40, [3]=0x50}},[2]={['ppq']=6624.0, ['buf']={[1]=0xb0, [2]=0x40, [3]=0x50}}}"
local function stringToTable(str)
    local f = load("return "..str)
    return f()
end
-- reaper.ShowConsoleMsg(events_string)
t_t = stringToTable(events_string)

for i,v in ipairs(t_t) do
    -- reaper.ShowConsoleMsg(string.format('\n%s:%s', i, v))
    result = reaper.MIDI_InsertTextSysexEvt(
        take,
        false,
        false,
        tonumber(v['ppq']),
        -1,
        -- midiBuf
        bytesToString(v['buf'])
    )
end


