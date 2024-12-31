class Config:
    def __init__(self):
        self.config = {}
        self.load()
    
    def load(self):
        try:
            with open('/config.ini', 'r') as f:
                current_section = ''
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if line.startswith('[') and line.endswith(']'):
                        current_section = line[1:-1]
                        self.config[current_section] = {}
                    elif '=' in line:
                        key, value = line.split('=', 1)
                        self.config[current_section][key.strip()] = value.strip()
        except:
            pass
    
    def get(self, section, key, default=None):
        return self.config.get(section, {}).get(key, default)
    
    def set(self, section, key, value):
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.save()
    
    def save(self):
        try:
            with open('/config.ini', 'w') as f:
                for section, items in self.config.items():
                    f.write(f"[{section}]\n")
                    for key, value in items.items():
                        f.write(f"{key}={value}\n")
                    f.write("\n")
        except Exception as e:
            print(f"保存配置文件失败: {e}") 