import qrcode

i = qrcode.make("abcdefghijklmnop")
i.save("test_file.png")
