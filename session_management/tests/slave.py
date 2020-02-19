from session_management.connections import jack_backend as jb

back = jb.JackBackend(
    '192.168.2.2',
    'jackd -R -S -d net -a 192.168.2.2 -p 9002 -n "192.168.2.2"',
    is_master=False
)
