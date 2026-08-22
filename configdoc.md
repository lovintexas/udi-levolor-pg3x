# Configure the Levolor Plugin

This plugin provides local control of Levolor motorized blinds through a Levolor InMotion gateway.

## Before configuring the plugin

1. Install the **Levolor InMotion** app on your phone and use it to configure your gateway and blinds.

2. Obtain the **gateway key**:
   - Open the **About** page in the InMotion app.
   - Tap the About/version area **5 times**.
   - The app will reveal the gateway key.

3. Find the gateway's **IP address** on your local network.
   - Look in your router's connected-device or DHCP-client list.
   - Some gateways may appear with a hostname beginning with `USB-Bridge_`.
   - Some network equipment may identify the manufacturer as **Feit** or identify the device as a **Feit Smart Plug**.
   - Creating a DHCP reservation for the gateway is recommended so its IP address does not change.

## Custom Configuration Parameters

Set `gateway_ip` to the local IPv4 address of your Levolor InMotion gateway.

Example: `192.168.1.100`

Set `gateway_key` to the gateway key obtained from the InMotion app.

The gateway key will look similar to:

`xxxxxxxx-xxxx-xx`

After entering both values, click **Save** on the Configuration page.

Then restart the plugin. The controller should connect to the gateway and the blinds should be discovered automatically.

The discovered blinds may be renamed as desired in the IoX Admin Console.

## Security

Treat the gateway key as a credential. Do not include it in screenshots, logs, forum posts, GitHub issues, or support requests.
