-- argument passed to the script
-- "true" if the script has to remove
-- completed works.
local remove_if_done = tostring(KEYS[1])

-- list of WorkIDs
local keys = redis.call("KEYS", "*")

local result = {}

-- iterating over the list
for _, key in ipairs(keys) do
    -- getting the full object
    local value = redis.call("HGETALL", key)
    local current_work = {}

    -- parsing the result
    for index = 1, #value, 2 do
        local field_name = value[index]
        local field_value = value[index + 1]

        current_work[field_name] = field_value

        -- if have to remove, and it's finished then
        -- delete it
        if remove_if_done == "true" then
            if field_name == "Status" and field_value == "Executed" then
                redis.call("DEL", key)
            end
        end
    end
    result[key] = current_work
end

-- encoding the result
return cjson.encode(result)
