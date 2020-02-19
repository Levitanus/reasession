import jack
from time import sleep


def update(client: jack.Client) -> None:

    print(
        f'''
        graph changed:
            inports:
                {client.get_ports(is_audio=True,is_input=True)}
            outports:
                {client.get_ports(is_audio=True,is_output=True)}
            midi_inports:
                {client.get_ports(is_midi=True,is_input=True)}
            midi_outports:
                {client.get_ports(is_midi=True,is_output=True)}
        '''
    )


cl = jack.Client('listener', no_start_server=True)
cl.set_graph_order_callback(lambda: update(cl))
cl.activate()

for i in range(20):
    sleep(1)
    print(i)
cl.deactivate()
