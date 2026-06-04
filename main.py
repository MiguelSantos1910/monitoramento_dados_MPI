from interface import AppPLC

if __name__ == "__main__":
    app = AppPLC()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()

#Bibliotecas para baixar: pip install python-snap7 matplotlib  python -m pip install "pymongo[srv]"