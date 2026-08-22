import random


class Heart:
    character: str = "h"
    weight: int = 0
    win_description: str = ""

    def __init__(
        self, character: str = "h", weight: int = 0, win_description: str = ""
    ):
        self.character = character
        self.weight = weight
        self.win_description = win_description


class HeartsPool:
    hearts: list[Heart]

    def __init__(self, hearts: list[Heart] = []):
        self.hearts = hearts

    def get_random(self) -> Heart:
        if not self.hearts:
            raise IndexError("No hearts available")
        return random.choices(
            self.hearts, weights=[h.weight for h in self.hearts], k=1
        )[0]

    def get_weights_sum(self) -> int:
        ans = 0
        for heart in self.hearts:
            ans += heart.weight

        return ans


hearts_pool = HeartsPool(
    hearts=[
        Heart("❤️‍🩹", 1200, "обычное сердечко"),
        Heart("🩷", 1200, "обычное сердечко"),
        Heart("🖤", 1200, "обычное сердечко"),
        Heart("💜", 1200, "обычное сердечко"),
        Heart("🩶", 1000, "необычное сердечко"),
        Heart("🤍", 1000, "необычное сердечко"),
        Heart("🤎", 1000, "необычное сердечко"),
        Heart("💛", 400, "редкое сердечко"),
        Heart("🧡", 400, "редкое сердечко"),
        Heart("❤️", 400, "редкое сердечко"),
        Heart("🩵", 200, "очень редкое сердечко"),
        Heart("💙", 200, "очень редкое сердечко"),
        Heart("💕", 100, "эпическое сердечко"),
        Heart("💞", 100, "эпическое сердечко"),
        Heart("💘", 100, "эпическое сердечко"),
        Heart("💓", 80, "мифическое сердечко"),
        Heart("💗", 80, "мифическое сердечко"),
        Heart("💖", 80, "мифическое сердечко"),
        Heart("💝", 25, "ЛЕГЕНДАРНОЕ СЕРДЕЧКО!!!"),
        Heart("❣️", 25, "ЛЕГЕНДАРНОЕ СЕРДЕЧКО!!!"),
        Heart(
            "❤️‍🔥",
            10,
            "НЕВОЗМОЖНО ПОЛУЧИМОЕ СЕРДЕЧКО!!!",
        ),
    ]
)
