import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk
import chess
from ChessEngine import Engine  # Engine sınıfını doğru şekilde içe aktarın

class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Satranç Oyunu")
        self.board = chess.Board()
        self.squares = {}
        self.images = {}
        self.selected_square = None
        self.highlighted_squares = []  # Vurgulanan kareleri takip et
        self.player_color = None
        self.engine = None
        self.ask_player_color()  # Oyuncu rengini sor
        self.create_board()
        self.load_images()
        self.update_board()

        # Eğer motor beyaz oynuyorsa, motorun ilk hamlesini yap
        if self.player_color == chess.BLACK:
            self.engine_move()

    def ask_player_color(self):
        # Kullanıcıdan beyaz mı siyah mı oynamak istediğini sor
        color_choice = simpledialog.askstring(
            "Renk Seçimi", 
            "Hangi rengi oynamak istersiniz? (beyaz/siyah)"
        )

        if color_choice and color_choice.lower() == "beyaz":
            self.player_color = chess.WHITE
            self.engine = Engine(self.board, maxDepth=3, color=chess.BLACK)
        elif color_choice and color_choice.lower() == "siyah":
            self.player_color = chess.BLACK
            self.engine = Engine(self.board, maxDepth=3, color=chess.WHITE)
        else:
            # Varsayılan olarak beyaz oynat
            self.player_color = chess.WHITE
            self.engine = Engine(self.board, maxDepth=3, color=chess.BLACK)

    def create_board(self):
        # Satranç tahtası için 8x8 kareler oluştur
        for row in range(8):
            for col in range(8):
                color = "white" if (row + col) % 2 == 0 else "gray"
                frame = tk.Frame(self.root, width=80, height=80, bg=color, highlightbackground="black", highlightthickness=1)
                frame.grid(row=row, column=col)
                frame.bind("<Button-1>", lambda event, r=row, c=col: self.on_square_click(r, c))
                self.squares[(row, col)] = frame

    def load_images(self):
        # Taş resimlerini yükle
        piece_map = {
            "P": "w/p.png", "R": "w/r.png", "N": "w/n.png", "B": "w/b.png", "Q": "w/q.png", "K": "w/k.png",
            "p": "b/p.png", "r": "b/r.png", "n": "b/n.png", "b": "b/b.png", "q": "b/q.png", "k": "b/k.png"
        }
        for piece, path in piece_map.items():
            image = Image.open(f"pieces/{path}")
            image = image.resize((80, 80), Image.Resampling.LANCZOS)
            self.images[piece] = ImageTk.PhotoImage(image)

    def update_board(self):
        # Tahtayı güncellemek için sadece değişen kareleri kontrol et
        self.reset_highlighted_squares()  # Önce vurgulamaları sıfırla

        for (row, col), frame in self.squares.items():
            square_index = (7 - row) * 8 + col
            piece = self.board.piece_at(square_index)

            # Karedeki mevcut widget'ları kontrol et
            current_widgets = frame.winfo_children()
            current_piece = current_widgets[0] if current_widgets else None

            if piece:
                piece_image = self.images[piece.symbol()]
                if current_piece is None or current_piece.cget("image") != str(piece_image):
                    # Eğer karede taş yoksa ya da taş değişmişse, güncelle
                    for widget in current_widgets:
                        widget.destroy()  # Eski taşı kaldır
                    label = tk.Label(frame, image=piece_image, bg=frame["bg"])
                    label.pack()
                    label.bind("<Button-1>", lambda event, r=row, c=col: self.on_square_click(r, c))
            else:
                # Eğer karede taş yoksa, mevcut widget'ı temizle
                if current_widgets:
                    for widget in current_widgets:
                        widget.destroy()

        # Şah tehdit altındaysa vurgula
        self.highlight_king_in_check()

        # Oyun bitiş durumunu kontrol et
        self.check_game_over()

    def reset_highlighted_squares(self):
        # Vurgulanan karelerin renklerini sıfırla
        for row, col in self.highlighted_squares:
            color = "white" if (row + col) % 2 == 0 else "gray"
            square_frame = self.squares[(row, col)]
            square_frame.config(bg=color)  # Kareyi sıfırla

            # Karede taş varsa, taşın arka planını da sıfırla
            for widget in square_frame.winfo_children():
                widget.config(bg=color)

        self.highlighted_squares = []  # Listeyi temizle


    def highlight_legal_moves(self, square_index):
        # Seçilen taşın yasal hareketlerini vurgula
        selected_piece = self.board.piece_at(square_index)

        if not selected_piece:
            return  # Seçili karede taş yoksa hiçbir şey yapma

        for move in self.board.legal_moves:
            if move.from_square == square_index:
                target_row = 7 - (move.to_square // 8)
                target_col = move.to_square % 8
                self.squares[(target_row, target_col)].config(bg="green")  # Yasal hamleleri yeşil renkle vurgula
                self.highlighted_squares.append((target_row, target_col))

    def highlight_king_in_check(self):
        # Şah tehdit altındaysa şahın bulunduğu kareyi kırmızı yap
        if self.board.is_check():
            king_square = self.board.king(self.board.turn)  # Şahın bulunduğu kare
            if king_square is not None:
                king_row = 7 - (king_square // 8)
                king_col = king_square % 8
                square_frame = self.squares[(king_row, king_col)]
                square_frame.config(bg="red")  # Kırmızıya boya
                for widget in square_frame.winfo_children():
                    widget.config(bg="red")
                self.highlighted_squares.append((king_row, king_col))

    def highlight_capturable_pieces(self, square_index):
        # Her çağrı sırasında listeyi sıfırla
        capturable_squares = []  # Yiyebileceğiniz taşların karelerini tutmak için bir liste

        # Yasal hamleler arasında yiyebileceğiniz taşları bul
        for move in self.board.legal_moves:
            if self.board.piece_at(move.to_square) and self.board.piece_at(move.to_square).color != self.board.turn:
                target_row = 7 - (move.to_square // 8)
                target_col = move.to_square % 8
                capturable_squares.append((target_row, target_col))

        # Kareleri sarıya boyama işlemi
        for row, col in capturable_squares:
            square_frame = self.squares[(row, col)]
            square_frame.config(bg="yellow")  # Kareyi sarıya boya

            # Karede taş varsa, taşın arka planını da güncelle
            for widget in square_frame.winfo_children():
                widget.config(bg="yellow")

            self.highlighted_squares.append((row, col))  # Daha sonra temizlemek için listeye ekle
            self.capturable_squares = []



    def on_square_click(self, row, col):
        print(f"Kareye tıklandı: Satır {row}, Sütun {col}")

        if self.board.turn != self.player_color:
            print("Sıra oyuncuda değil.")
            return  # Oyuncunun sırası değilse tıklamaları yok say

        square_index = (7 - row) * 8 + col
        if self.selected_square is None:
            # İlk tıklama: taş seçimi
            self.selected_square = square_index
            print(f"Seçilen kare: {self.selected_square}")

            # Önceki vurguları temizlemeden her iki fonksiyonu çağır
            self.reset_highlighted_squares()
            self.highlight_legal_moves(square_index)  # Yasal hareketleri vurgula
            self.highlight_capturable_pieces(square_index)  # Yiyebileceğiniz taşları vurgula
        else:
            # İkinci tıklama: hareket yap
            print(f"Hedef kare: {square_index}")
            move = chess.Move(self.selected_square, square_index)
            if move in self.board.legal_moves:
                self.board.push(move)  # Kullanıcı hamlesini tahtaya uygula
                self.reset_highlighted_squares()  # Hamle sonrası tüm vurgulamaları sıfırla
                self.update_board()  # Tahtayı güncelle
                self.engine_move()  # Kullanıcı hamlesinden hemen sonra motor hamlesi yap
            else:
                print(f"Geçersiz hamle: {self.selected_square} -> {square_index}")
                self.reset_highlighted_squares()  # Geçersiz hamleden sonra vurgulamaları sıfırla
            self.selected_square = None  # Seçimi sıfırla


    def engine_move(self):
        if not self.board.is_game_over() and self.board.turn != self.player_color:
            best_move = self.engine.getBestMove()  # Motorun en iyi hamlesini al
            if best_move:
                self.board.push(best_move)  # Hamleyi tahtaya uygula
                self.update_board()

    def check_game_over(self):
        # Oyun bitiş durumunu kontrol et
        if self.board.is_checkmate():
            if self.board.turn == self.player_color:
                self.show_game_over_message("Kaybettiniz!")
            else:
                self.show_game_over_message("Kazandınız!")
        elif self.board.is_stalemate():
            self.show_game_over_message("Berabere!")
        elif self.board.is_insufficient_material():
            self.show_game_over_message("Berabere! Yetersiz materyal.")

    def show_game_over_message(self, message):
        # Oyun bitiş mesajını göster ve yeniden başlatma seçeneği sun
        play_again = messagebox.askyesno("Oyun Bitti", f"{message}\nYeniden oynamak ister misiniz?")
        if play_again:
            self.restart_game()
        else:
            self.root.destroy()

    def restart_game(self):
        # Oyunu yeniden başlat
        self.board = chess.Board()
        self.selected_square = None
        self.reset_highlighted_squares()

        # Kullanıcıya tekrar renk seçme hakkı tanı
        self.ask_player_color()

        self.update_board()

        # Eğer motor beyaz oynuyorsa, motorun ilk hamlesini yap
        if self.player_color == chess.BLACK:
            self.engine_move()


if __name__ == "__main__":
    root = tk.Tk()
    gui = ChessGUI(root)
    root.mainloop()
