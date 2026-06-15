# -*- coding: utf-8 -*-
# Generated-compatible minimal protobuf surface for device_controls.Controls.
from __future__ import annotations

from google.protobuf import descriptor_pb2
from google.protobuf import descriptor_pool
from google.protobuf import message_factory
from google.protobuf import symbol_database

_sym_db = symbol_database.Default()

fd = descriptor_pb2.FileDescriptorProto()
fd.name = "device_controls/controls.proto"
fd.package = "device_controls"
fd.syntax = "proto3"
fd.dependency.append("google/protobuf/empty.proto")


def _message(name: str):
    msg = fd.message_type.add()
    msg.name = name
    return msg


def _field(msg, name: str, number: int, field_type: int, type_name: str = ""):
    field = msg.field.add()
    field.name = name
    field.number = number
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = field_type
    if type_name:
        field.type_name = type_name
    return field


req = _message("SetDeviceValueRequest")
_field(req, "type", 1, descriptor_pb2.FieldDescriptorProto.TYPE_INT32)
_field(req, "value", 2, descriptor_pb2.FieldDescriptorProto.TYPE_INT32)

event = _message("Event")
_field(event, "type", 1, descriptor_pb2.FieldDescriptorProto.TYPE_INT32)
_field(event, "value", 2, descriptor_pb2.FieldDescriptorProto.TYPE_INT32)

status = _message("GetDeviceStatusResponse")

iot = status.nested_type.add()
iot.name = "IotStatus"
_field(iot, "fw_version", 1, descriptor_pb2.FieldDescriptorProto.TYPE_INT32)
_field(iot, "alarms", 2, descriptor_pb2.FieldDescriptorProto.TYPE_BYTES)

main = status.nested_type.add()
main.name = "MainStatus"

setpoint = main.nested_type.add()
setpoint.name = "SetpointStatus"
for index, name in enumerate(("value", "min", "max", "step", "offset"), start=1):
    _field(setpoint, name, index, descriptor_pb2.FieldDescriptorProto.TYPE_INT32)

calendar = main.nested_type.add()
calendar.name = "CalendarStatus"
_field(calendar, "is_active", 1, descriptor_pb2.FieldDescriptorProto.TYPE_BOOL)
_field(
    calendar,
    "override_until_minutes_epoch",
    2,
    descriptor_pb2.FieldDescriptorProto.TYPE_INT32,
)

due = main.nested_type.add()
due.name = "DuepuntozeroStatus"
_field(
    due,
    "calendar",
    1,
    descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
    ".device_controls.GetDeviceStatusResponse.MainStatus.CalendarStatus",
)
_field(due, "power_state", 2, descriptor_pb2.FieldDescriptorProto.TYPE_BOOL)
_field(
    due,
    "temperature_setpoint",
    3,
    descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
    ".device_controls.GetDeviceStatusResponse.MainStatus.SetpointStatus",
)
_field(due, "room_temperature", 4, descriptor_pb2.FieldDescriptorProto.TYPE_INT32)
_field(due, "operation_mode", 5, descriptor_pb2.FieldDescriptorProto.TYPE_INT32)
_field(due, "fan_speed", 6, descriptor_pb2.FieldDescriptorProto.TYPE_INT32)
_field(due, "flap", 7, descriptor_pb2.FieldDescriptorProto.TYPE_BOOL)
_field(due, "hotel_mode", 8, descriptor_pb2.FieldDescriptorProto.TYPE_BOOL)
_field(due, "keyboard_lock", 9, descriptor_pb2.FieldDescriptorProto.TYPE_BOOL)
_field(due, "mode_lock", 10, descriptor_pb2.FieldDescriptorProto.TYPE_BOOL)
_field(due, "has_uv_lamp", 11, descriptor_pb2.FieldDescriptorProto.TYPE_BOOL)
_field(due, "uv_lamp", 12, descriptor_pb2.FieldDescriptorProto.TYPE_BOOL)
_field(due, "temperature_unit", 13, descriptor_pb2.FieldDescriptorProto.TYPE_INT32)
_field(due, "has_air_exchange", 14, descriptor_pb2.FieldDescriptorProto.TYPE_BOOL)
_field(due, "air_exchange", 15, descriptor_pb2.FieldDescriptorProto.TYPE_BOOL)
_field(due, "has_bms", 16, descriptor_pb2.FieldDescriptorProto.TYPE_BOOL)
_field(due, "additional_data", 17, descriptor_pb2.FieldDescriptorProto.TYPE_BYTES)

_field(main, "fw_version", 1, descriptor_pb2.FieldDescriptorProto.TYPE_INT32)
_field(main, "serial_number", 2, descriptor_pb2.FieldDescriptorProto.TYPE_STRING)
_field(main, "alarms", 3, descriptor_pb2.FieldDescriptorProto.TYPE_BYTES)
_field(
    main,
    "duepuntozero_status",
    4,
    descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
    ".device_controls.GetDeviceStatusResponse.MainStatus.DuepuntozeroStatus",
)

_field(
    status,
    "iot_status",
    1,
    descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
    ".device_controls.GetDeviceStatusResponse.IotStatus",
)
_field(
    status,
    "main_status",
    2,
    descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
    ".device_controls.GetDeviceStatusResponse.MainStatus",
)

pool = descriptor_pool.Default()
try:
    DESCRIPTOR = pool.AddSerializedFile(fd.SerializeToString())
except TypeError:
    DESCRIPTOR = pool.FindFileByName(fd.name)

SetDeviceValueRequest = message_factory.GetMessageClass(
    DESCRIPTOR.message_types_by_name["SetDeviceValueRequest"]
)
Event = message_factory.GetMessageClass(DESCRIPTOR.message_types_by_name["Event"])
GetDeviceStatusResponse = message_factory.GetMessageClass(
    DESCRIPTOR.message_types_by_name["GetDeviceStatusResponse"]
)

_sym_db.RegisterMessage(SetDeviceValueRequest)
_sym_db.RegisterMessage(Event)
_sym_db.RegisterMessage(GetDeviceStatusResponse)
