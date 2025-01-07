try:
    import os
except ImportError:
    import uos as os

class Config:
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = {}
        self.load()
        
    def load(self):
        """加载配置文件"""
        self.config = {}
        try:
            # 尝试打开文件，如果不存在就跳过
            with open(self.config_file, 'r') as f:
                current_section = None
                for line in f:
                    line = line.strip()
                    if line.startswith('[') and line.endswith(']'):
                        # 新的section
                        current_section = line[1:-1]
                        self.config[current_section] = {}
                    elif '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if current_section:
                            self.config[current_section][key] = value
        except OSError:
            # 文件不存在或其他IO错误时忽略
            pass

        # 确保必要的section存在
        if 'bluetooth' not in self.config:
            self.config['bluetooth'] = {}
            
    def save(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w') as f:
                for section, values in self.config.items():
                    f.write(f'[{section}]\n')
                    for key, value in values.items():
                        f.write(f'{key}={value}\n')
                    f.write('\n')
        except:
            pass
            
    def get(self, section, key, default=None):
        """获取配置值"""
        try:
            return self.config[section][key]
        except:
            return default
            
    def set(self, section, key, value):
        """设置配置值"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.save()
        
    def get_bluetooth_config(self):
        """获取蓝牙配置"""
        return {
            'uuid': self.get('bluetooth', 'uuid'),
            'tx_char': self.get('bluetooth', 'tx_char'),
            'rx_char': self.get('bluetooth', 'rx_char'),
            'device_name': self.get('bluetooth', 'device_name'),
            'device_addr': self.get('bluetooth', 'device_addr')
        }
        
    def set_bluetooth_config(self, uuid, tx_char, rx_char, device_name=None, device_addr=None):
        """设置蓝牙配置"""
        self.set('bluetooth', 'uuid', str(uuid))
        self.set('bluetooth', 'tx_char', str(tx_char))
        self.set('bluetooth', 'rx_char', str(rx_char))
        if device_name:
            self.set('bluetooth', 'device_name', device_name)
        if device_addr:
            self.set('bluetooth', 'device_addr', device_addr) 