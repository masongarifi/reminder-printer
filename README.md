# Reminder Printer

A standalone local Flask application that accepts Apple Reminders data, formats it
as a native 42-column receipt checklist, and prints it through USB to an Epson
thermal printer with feed and cut. It has no runtime cloud dependency and shares
no code or service configuration with other projects.

## Repository structure

`app.py` contains the web/API routes, `formatter.py` parses and lays out reminders,
`printer.py` owns locked USB access, and `config.py` reads environment settings.
The `templates/` and `static/` directories provide the dependency-free mobile UI.
`systemd/`, `scripts/`, and `tests/` contain deployment, operations, and tests.

## Raspberry Pi installation

Install Git, Python venv support, libusb, and mDNS, then clone and install:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv libusb-1.0-0 avahi-daemon
cd ~
git clone https://github.com/masongarifi/reminder-printer.git
cd reminder-printer
chmod +x scripts/*.sh
./scripts/install.sh
```

The installer uses the invoking user. To choose another existing account:

```bash
REMINDER_PRINTER_USER=pi ./scripts/install.sh
```

It creates an isolated `.venv`, installs `/etc/systemd/system/reminder-printer.service`,
enables it at boot, and starts it. It never edits another repository or service.

## Find and configure the Epson USB IDs

Connect and power on the printer, then run:

```bash
lsusb
```

Find the Epson line, such as `ID 04b8:xxxx Seiko Epson Corp.`. The four hex digits
before and after the colon are the vendor and product IDs. Edit the environment file:

```bash
sudo nano /etc/reminder-printer.env
```

Set, using the values reported by `lsusb`:

```dotenv
REMINDER_PRINTER_USB_VENDOR_ID=0x04b8
REMINDER_PRINTER_USB_PRODUCT_ID=0xYOUR_PRODUCT_ID
```

Never commit machine-specific IDs or a real `.env`. Available settings are:

| Variable | Default | Purpose |
|---|---:|---|
| `REMINDER_PRINTER_HOST` | `0.0.0.0` | Listen address |
| `REMINDER_PRINTER_PORT` | `5055` | Local TCP port |
| `REMINDER_PRINTER_WIDTH` | `42` | Printable characters |
| `REMINDER_PRINTER_USB_VENDOR_ID` | unset | Epson vendor ID |
| `REMINDER_PRINTER_USB_PRODUCT_ID` | unset | Epson product ID |
| `REMINDER_PRINTER_INCLUDE_COMPLETED` | `false` | Default filtering |
| `REMINDER_PRINTER_FEED_LINES` | `3` | Lines before cut |

After changes:

```bash
sudo systemctl restart reminder-printer
```

## Use and operate

Open `http://receiptpi.local:5055/` on the local network, paste reminders, preview,
and print. The hostname assumes the Pi is named `receiptpi`.

```bash
systemctl status reminder-printer
journalctl -u reminder-printer -n 100 --no-pager
journalctl -u reminder-printer -f
sudo systemctl restart reminder-printer
./scripts/test-print.sh
./scripts/update.sh
```

Health and API examples:

```bash
curl http://receiptpi.local:5055/api/health
curl -H 'Content-Type: text/plain' \
  --data-binary $'Grocery List\n[ ] Milk\n[x] Return package' \
  'http://receiptpi.local:5055/api/preview-reminders'
curl -H 'Content-Type: application/json' \
  -d '{"title":"Grocery List","include_completed":false,"items":[{"text":"Milk","completed":false},{"text":"Return package","completed":true}]}' \
  http://receiptpi.local:5055/api/print-reminders
```

Plain text may also pass `?title=Grocery%20List&include_completed=false`. JSON and
form submissions return JSON; preview returns `receipt`, while print returns a
success message or a clear HTTP 503 printer error.

## Apple Shortcut: Print Reminder List

Action names can vary slightly by OS release. These are the current Shortcuts action
names; use **Get Contents of URL** with its expanded options.

### Method 1: Share Sheet text

1. Create a shortcut named **Print Reminder List**.
2. Open shortcut details, enable **Show in Share Sheet**, and limit input to **Text**.
3. Add **Ask for Input**; choose Text, prompt `Reminder list title`, default `Reminders`.
4. Add **URL** with `http://receiptpi.local:5055/api/print-reminders`.
5. Add **Get Contents of URL**. Set Method to POST, Request Body to Form, and add:
   `title` = the **Provided Input** from Ask for Input, and `text` = **Shortcut Input**.
6. Add **Get Dictionary from Input** using the result.
7. Add **Get Dictionary Value** for `ok`, followed by **If**.
8. In the true branch, add **Show Notification** with `Reminder list printed`.
9. In Otherwise, get dictionary value `error` and add **Show Alert** with that value.

### Method 2: Select a Reminders list

1. Create a shortcut named **Print Reminder List**.
2. Add **Get Lists** (Reminders), then **Choose from List**.
3. Add **Find Reminders** and set its filter to `List is` the chosen list.
4. Add **Repeat with Each** over the found reminders.
5. Inside Repeat, add **Get Details of Reminders** for `Title`, then again for
   `Is Completed`.
6. Add **Dictionary** with `text` = Title and `completed` = Is Completed, then
   **Add to Variable** named `Reminder Items`.
7. After Repeat, add **Dictionary** with `title` = Name of the chosen list,
   `include_completed` = `false`, and `items` = `Reminder Items`.
8. Add **URL** with `http://receiptpi.local:5055/api/print-reminders`.
9. Add **Get Contents of URL**: Method POST, Request Body JSON, using that Dictionary.
10. Get dictionary value `ok` and use **If**. Show **Show Notification** on success;
    otherwise get `error` and use **Show Alert**.

On iPhone, allow the shortcut local-network access if prompted. On Mac, ensure the
Mac and Pi are on the same network.

## Troubleshooting

**Printer not found:** run `lsusb`, verify both configured IDs, cable, power, then:

```bash
sudo systemctl restart reminder-printer
journalctl -u reminder-printer -n 100 --no-pager
```

**USB permission denied:** identify the IDs with `lsusb`, then create a udev rule
(substitute the exact lowercase IDs without `0x`):

```bash
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="04b8", ATTR{idProduct}=="YOUR_ID", MODE="0660", GROUP="lp"' | sudo tee /etc/udev/rules.d/99-reminder-printer.rules
sudo usermod -aG lp "$(whoami)"
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Log out and back in, reconnect the printer, and restart the service. Avoid running
two printer applications simultaneously; this service serializes its own jobs, but
cannot lock unrelated processes.

**`receiptpi.local` does not resolve:** confirm the hostname and Avahi:

```bash
hostname
systemctl status avahi-daemon
hostname -I
```

Use `http://PI_IP_ADDRESS:5055/` with the address from `hostname -I`, or set the Pi
hostname with `sudo hostnamectl set-hostname receiptpi` and reboot.

**Port already used:**

```bash
sudo ss -ltnp | grep ':5055'
sudo nano /etc/reminder-printer.env
sudo systemctl restart reminder-printer
```

Choose another `REMINDER_PRINTER_PORT` and use it in the URL.

**Service fails to start:**

```bash
sudo systemctl daemon-reload
sudo systemctl status reminder-printer --no-pager
sudo journalctl -u reminder-printer -b --no-pager
```

Confirm the repository was not moved after installation and rerun `./scripts/install.sh`
if it was.

## Development

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt pytest
pytest -q
REMINDER_PRINTER_PORT=5055 flask --app app run --host 0.0.0.0
```

