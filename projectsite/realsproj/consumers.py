import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ScanConsumer(AsyncWebsocketConsumer):
    async def connect(self):
       
        await self.channel_layer.group_add("scan_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("scan_group", self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        barcode = data.get("barcode")

        await self.channel_layer.group_send(
            "scan_group",
            {
                "type": "scan_message",
                "barcode": barcode
            }
        )

    async def scan_message(self, event):
        barcode = event["barcode"]

       
        await self.send(text_data=json.dumps({
            "barcode": barcode
        }))
