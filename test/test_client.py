# coding=utf-8
import argparse
from pandorarpc.client import Client, DEFAULT_INTERFACE


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--interface', help='Connect interface')
    parser.set_defaults(interface=DEFAULT_INTERFACE)
    options = parser.parse_args()
    interface = options.interface

    c = Client()
    c.connect(interface)

    print c.get_name(1, 'appname')
    print c.get_state(1, 'appstate')

    # token = c.generate_token()
    # print c.create_group(token, 'g1')
    # print c.create_app(0x1000, 'pandora1', 'app')
    # print c.delete_app(1)
    # print c.update_group_name(0x4000, 'group1')

    # update_1 = c.begin_update(1)
    # try:
    #     c.update_name(update_1, "aaa1")
    #     c.update_category(update_1, "bbb1")
    # except Exception as e:
    #     c.abort_update(update_1)
    # else:
    #     print c.execute_update(update_1)

    c.disconnect()

if __name__ == "__main__":
    main()