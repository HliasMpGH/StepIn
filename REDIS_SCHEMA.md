# Redis Schema Documentation

This document outlines the Redis key structure and data types used in the system.

## Key Structure

### Meeting Management
| Key Pattern | Type | Description | Example |
|-------------|------|-------------|---------|
| `active_meetings` | Set | Collection of all active meeting IDs | `{"1", "2", "3"}` |
| `meeting:<id>` | Hash | Meeting details | `meeting:2 → {title: "Team Sync", description: "Weekly sync", t1: "2023-04-01T09:00", t2: "2023-04-01T10:00"}` |
| `meeting_positions` | Geo Set | Geospatial index of meetings | `GEOADD meeting_positions 73.5 40.7 "1" 74.0 41.2 "2"` |

### User Management
| Key Pattern | Type | Description | Example |
|-------------|------|-------------|---------|
| `participants:<meeting_id>` | Set | Users invited to a meeting | `participants:3 → {"alice@example.com", "bob@example.com"}` |
| `joined:<meeting_id>` | Set | Users currently in a meeting | `joined:3 → {"alice@example.com"}` |
| `user_joined_meeting:<email>` | String | ID of meeting user has joined | `user_joined_meeting:alice@example.com → "3"` |
| `user_participate_meetings:<email>` | Set | All meetings where user is a participant | `user_participate_meetings:alice@example.com → {"1", "2", "3"}` |

### Chat Functionality
| Key Pattern | Type | Description | Example |
|-------------|------|-------------|---------|
| `chat:<meeting_id>` | List | Chat messages for a meeting | `chat:3 → [{email: "alice@example.com", text: "Hello", timestamp: 1617249600}]` |
| `chat:<meeting_id>:<email>` | List | Indices of user messages in meeting chat | `chat:3:alice@example.com → [0, 3, 5]` |

## Data Relationships

- Each meeting in `active_meetings` has corresponding details in `meeting:<id>` hash, a geospatial location in `meeting_positions` and a list of participants in `participants:<meeting_id>`
- Currently joined users are tracked in `joined:<meeting_id>`
- Each joined user has their current meeting stored in `user_joined_meeting:<email>`
- Each user has a list of meetings they are part of in `user_participate_meetings:<email>` (acts as a secondary index of `participants:<meeting_id>`)
- Chat messages are stored chronologically in `chat:<meeting_id>`
- Each user's message positions are tracked in `chat:<meeting_id>:<email>`

## Usage Patterns

### Activating a Meeting in Redis
1. Add meeting ID to `active_meetings`
2. Set meeting details in `meeting:<id>`
3. Add location to `meeting_positions`
4. Add participants to `participants:<meeting_id>`
5. Add meeting ID to each participant's `user_participate_meetings:<email>`

### User Joining a Meeting
1. Add user to `joined:<meeting_id>`
2. Set user's `user_joined_meeting:<email>` to meeting ID

### User Sending a Chat Message
1. Add message to `chat:<meeting_id>` list
2. Add message index to `chat:<meeting_id>:<email>` list

## Finding Nearby Meetings
When a user with email `e` and location `(x,y)` wants to see active events nearby:

```python
# 1. Get meetings near the user's location (within 100m radius)
nearby_meeting_ids = GEORADIUS meeting_positions x y 100 m

# 2. Filter for meetings the user is a participant of
user_meetings_id = SMEMBERS user_participate_meetings:{e}
nearby_valid_meetings = INTERSECTION(nearby_meeting_ids, user_meetings_id)
```

## User Leaving a Meeting
When a user with email `e` leaves a meeting with ID `m`:

```python
# 1. Remove user from the joined set of the meeting
SREM joined:{m} e

# 2. Clear the user's current joined meeting reference
DEL user_joined_meeting:{e}
```

## Deactivating a Meeting in Redis
When a meeting with ID `m` ends (gets removed from redis):

```python
# 1. Remove meeting from active meetings set
SREM active_meetings m

# 2. Remove meeting from geographical index
ZREM meeting_positions m

# 3. Remove all joined users
joined_users = SMEMBERS joined:{m}
for email in joined_users:
    DEL user_joined_meeting:{email}

# 4. For each participant, remove meeting from their list, and their chats indices
participants = SMEMBERS participants:{m}
for email in participants:
    SREM user_participate_meetings:{email} m
    DEL chat:{m}:{email}

# 5. Clean up meeting resources
DEL meeting:{m}
DEL participants:{m}
DEL joined:{m}
DEL chat:{m}
```

## Design Choices

### The `chat:id:email` Index Approach

The `chat:id:email` key structure represents an efficient indexing mechanism for retrieving a specific user's messages within a meeting's chat history. This approach offers significant advantages over alternative methods:

#### How It Works

- `chat:id` stores the complete chat history as a Redis list containing message objects: `{email: "user@example.com", text: "message content", timestamp: 1617249600}`
- `chat:id:email` stores only a list of indices (positions) where that user's messages appear in the main chat list: `[0, 5, 7]`

#### Benefits Over Alternative Approaches

##### Compared to filtering in application code:
- **Reduced data transfer**: Instead of fetching all messages and filtering in Python, we only retrieve the relevant indices and then the specific messages
- **Lower CPU usage**: Eliminates the need to iterate through potentially thousands of messages to find those from a specific user
- **Better scalability**: Performance remains consistent regardless of total chat history size

##### Compared to duplicate storage:
- **Reduced memory usage**: Each message is stored only once in the main chat list, with only small integer indices in the user-specific list
- **Data consistency**: No risk of inconsistencies that could occur when maintaining duplicate copies of messages

### The `user_participate_meetings:email` Approach

By using a secondary index on the `participants:id` key (that holds the participants of the meeting in a set), its easier to calculate the nearby meetings when a user requests it. More specifically, we only need to do a set intersection between the results of the `geosearch` (that returns the nearby meetings) and the `user_participate_meetings:email` (the meetings the user is a participant). If we did not include a `user_participate_meetings:email` key, we would have to iterate over the nearby meetings and check for each one, if the user is included in the participant list.

### The `meeting:id` Approach

When activating a meeting in redis, we distribute its details in 3 keys. `meeting:id`, `meeting_position` and `participants:id`. We do that in order to take advantage of some specific redis operations (instead of doing them using python). More specifically:

1. We do not save the (long, lat) attributes of a meeting in the hash of `meeting:id`, and instead save them in a <b>geospatial data structure</b> to do geo-operations faster (like finding nearby meetings).

2. We do not save the participants of a meeting in the hash `meeting:id`, and instead save them in a separate key, `participants:id`, so we can perform set operations easier.
