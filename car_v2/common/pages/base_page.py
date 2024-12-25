import lvgl as lv

class BasePage:
    def __init__(self, screen):
        self.screen = screen
        self.elements = []
        
    def init(self):
        pass
        
    def destroy(self):
        for element in self.elements:
            element.delete()
        self.elements.clear() 