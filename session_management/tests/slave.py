from session_management.connections import jack_backend as jb

back = jb.JackBackend(
    '192.168.2.2',
    'jackd -R -S -d net -a 192.168.2.1 -p 9002 -i 10 -o 0 -C 1 -P 2 -n 192.168.2.2  >/dev/null 2>&1 < /dev/null &',
    is_master=False
)
