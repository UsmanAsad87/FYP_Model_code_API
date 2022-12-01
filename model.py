from typing import List
from typing import Any
from dataclasses import dataclass
import json
@dataclass
class Date:
    $numberLong: str

    @staticmethod
    def from_dict(obj: Any) -> 'Date':
        _$numberLong = str(obj.get("$numberLong"))
        return Date(_$numberLong)

@dataclass
class Id:
    $oid: str

    @staticmethod
    def from_dict(obj: Any) -> 'Id':
        _$oid = str(obj.get("$oid"))
        return Id(_$oid)

@dataclass
class RecentTimeStamp:
    $date: Date

    @staticmethod
    def from_dict(obj: Any) -> 'RecentTimeStamp':
        _$date = Date.from_dict(obj.get("$date"))
        return RecentTimeStamp(_$date)

@dataclass
class Root:
    _id: Id
    name: str
    imgUrl: str
    recent_timeStamp: RecentTimeStamp
    recent_location: str
    timeStamps: List[TimeStamp]

    @staticmethod
    def from_dict(obj: Any) -> 'Root':
        __id = Id.from_dict(obj.get("_id"))
        _name = str(obj.get("name"))
        _imgUrl = str(obj.get("imgUrl"))
        _recent_timeStamp = RecentTimeStamp.from_dict(obj.get("recent_timeStamp"))
        _recent_location = str(obj.get("recent_location"))
        _timeStamps = [TimeStamp.from_dict(y) for y in obj.get("timeStamps")]
        return Root(__id, _name, _imgUrl, _recent_timeStamp, _recent_location, _timeStamps)

@dataclass
class Time:
    date: Date

    @staticmethod
    def from_dict(obj: Any) -> 'Time':
        _date = Date.from_dict(obj.get("date"))
        return Time(_date)

@dataclass
class TimeStamp:
    time: Time
    location: str

    @staticmethod
    def from_dict(obj: Any) -> 'TimeStamp':
        _time = Time.from_dict(obj.get("time"))
        _location = str(obj.get("location"))
        return TimeStamp(_time, _location)

# Example Usage
# jsonstring = json.loads(myjsonstring)
# root = Root.from_dict(jsonstring)

json={
  "_id": {
    "$oid": "63796236f15a2e6bf0327408"
  },
  "name": "Danish_Dept",
  "imgUrl": "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",
  "recent_timeStamp": {
    "$date": {
      "$numberLong": "1668917479802"
    }
  },
  "recent_location": "lab ICV",
  "timeStamps": [
    {
      "time": {
        "$date": {
          "$numberLong": "1668917404547"
        }
      },
      "location": "lab ICV"
    },
    {
      "time": {
        "$date": {
          "$numberLong": "1668917479802"
        }
      },
      "location": "lab ICV"
    }
  ]
}
root=Root.from_dict(json)