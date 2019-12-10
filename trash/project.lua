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
reaper.ClearConsole()
--------------------------------------------------------------------------------

project = {}

project.selected = 0
project.extname = 'SESSION_MANAGEMENT'

function project.registered()
    local retval, val = reaper.GetProjExtState(
        project.selected, project.extname, 'project_type')
    if retval == nil or val == '' then return nil end
    return val
end
function project.register(pr_type)
    assert(pr_type == 'master' or pr_type == 'slave',
        'can be only master or slave')
    reaper.SetProjExtState(project.selected, project.extname,
        'project_type', pr_type)
end
function project.unregister()
    reaper.SetProjExtState(project.selected, project.extname, 'project_type', '')
end
function project.get(key)
    local retval, val = reaper.GetProjExtState(
        project.selected, project.extname, key)
    if retval == nil or val == '' then return nil end
    return val
end
function project.set(key, val)
    reaper.SetProjExtState(project.selected, project.extname, key, val)
end
