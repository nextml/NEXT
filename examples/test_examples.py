import os

__dir__ = '/'.join(__file__.split('/')[:-1])
if __dir__ == '':
    __dir__ = '.'

def test_run_examples():
    zip_path = 'cartoon_cardinal/cap436.txt.zip'
    init_path = 'cartoon_cardinal/init.yaml'
    command = 'python launch.py {} {} --noS3'.format(init_path, zip_path)
    exit_status = os.system('cd {}; '.format(__dir__) + command)
    assert exit_status == 0

    zip_path = 'cartoon_dueling/cap436.txt.zip'
    init_path = 'cartoon_dueling/init.yaml'
    command = 'python launch.py {} {} --noS3'.format(init_path, zip_path)
    exit_status = os.system('cd {}; '.format(__dir__) + command)
    assert exit_status == 0

    zip_path = 'strange_fruit_triplet/strangefruit30.zip'
    init_path = 'strange_fruit_triplet/init.yaml'
    command = 'python launch.py {} {}'.format(init_path, zip_path)
    exit_status = os.system('cd {}; '.format(__dir__) + command)
    assert exit_status == 0

if __name__ == "__main__":
    test_run_examples()
