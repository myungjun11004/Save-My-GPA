import pygame
import sys
import random
import json
import os
from datetime import datetime

# ==========================================
# 1. 기본 설정 및 상수 정의
# ==========================================
FPS = 60
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (10, 25, 47)
GOLD = (255, 215, 0)
GRAY = (150, 150, 150)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)

# [수정됨] 텍스트용으로 눈에 띄는 색상 추가!
RED = (255, 50, 50)       
CYAN = (0, 150, 255)

BG_EXAM = (50, 10, 10)     
BG_VACATION = (10, 50, 10) 

COLOR_PLAYER = (0, 255, 0)       
COLOR_ITEM_COFFEE = (200, 100, 50) 
COLOR_ITEM_FREE = (0, 255, 255)  
COLOR_ENEMY_ASSIGN = (255, 0, 0) 
COLOR_ENEMY_ALCOHOL = (128, 0, 128) 

FILE_NAME = "gpa_history.json"

# ==========================================
# [AI Suggestion] DataManager 클래스 (파일 입출력 전담)
# ==========================================
class DataManager:
    def __init__(self, filename):
        self.filename = filename

    def load_scores(self):
        # 파일이 존재하면 읽어오고, 없으면 빈 리스트 반환
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []

    def save_score(self, name, gpa, is_graduated):
        scores = self.load_scores()
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # 새로운 기록 딕셔너리 생성
        new_record = {
            "name": name,
            "gpa": round(gpa, 2),
            "status": "졸업" if is_graduated else "제적",
            "date": date_str
        }
        scores.append(new_record)
        
        # GPA 기준으로 내림차순 정렬하여 저장
        scores.sort(key=lambda x: x["gpa"], reverse=True)
        
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(scores, f, indent=4, ensure_ascii=False)


# ==========================================
# 클래스 정의 (Player, Item, Enemy, FloatingText)
# ==========================================
class FloatingText(pygame.sprite.Sprite):
    # 아이템을 먹거나 피해를 입었을 때 떠오르는 텍스트 이펙트
    def __init__(self, x, y, text, color, font):
        super().__init__()
        self.image = font.render(text, True, color)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed_y = -2  # 위로 올라감
        self.life = 60     # 60프레임(1초) 동안 생존

    def update(self):
        self.rect.y += self.speed_y
        self.life -= 1
        if self.life <= 0:
            self.kill() # 수명이 다하면 스프라이트 그룹에서 자동 삭제

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        # --- [수정됨] 목표 크기를 60x60으로 설정 ---
        TARGET_SIZE = (60, 60) 
        
        try:
            self.img_good = pygame.image.load("player_good.png").convert_alpha()
            self.img_soso = pygame.image.load("player_soso.png").convert_alpha()
            self.img_bad = pygame.image.load("player_bad.png").convert_alpha()
            
            # [수정됨] 모든 이미지 크기를 60x60으로 늘림
            self.img_good = pygame.transform.scale(self.img_good, TARGET_SIZE)
            self.img_soso = pygame.transform.scale(self.img_soso, TARGET_SIZE)
            self.img_bad = pygame.transform.scale(self.img_bad, TARGET_SIZE)
            
            self.image = self.img_soso 
            
        except FileNotFoundError:
            print("캐릭터 이미지를 찾을 수 없어 네모로 대체합니다.")
            # [수정됨] 대체 네모도 60x60으로 변경
            self.image = pygame.Surface(TARGET_SIZE)
            self.image.fill((0, 255, 0)) 
            self.img_good = self.img_soso = self.img_bad = self.image

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
        self.speed = 5
        self.mental = 50  
        self.gpa = 2.5 

    # (update 함수는 그대로 유지)

    def update(self):
        # 1. 키보드 이동 로직 (기존과 동일)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]: self.rect.x += self.speed
        if keys[pygame.K_UP]: self.rect.y -= self.speed
        if keys[pygame.K_DOWN]: self.rect.y += self.speed

        # 화면 경계 막기 (기존과 동일)
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH: self.rect.right = SCREEN_WIDTH
        if self.rect.top < 0: self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT: self.rect.bottom = SCREEN_HEIGHT

        # --- [신규] 현재 GPA(학점)에 따라 캐릭터 표정/옷차림 바꾸기 ---
        if self.gpa >= 3.5:
            self.image = self.img_good  # 갓생 사는 중
        elif self.gpa >= 2.0:
            self.image = self.img_soso  # 평범한 학부생
        else:
            self.image = self.img_bad   # 유학 위기 (학사경고)
        # -----------------------------------------------------------

class Item(pygame.sprite.Sprite):
    def __init__(self, item_type, season="평시"):
        super().__init__()
        self.type = item_type
        
        # --- [수정됨] 아이템 목표 크기를 50x50으로 설정 ---
        ITEM_SIZE = (50, 50)
        
        try:
            if self.type == "coffee":
                self.image = pygame.image.load("coffee.png").convert_alpha()
                self.name = "커피"
            elif self.type == "free_period":
                self.image = pygame.image.load("bed.png").convert_alpha()
                self.name = "공강"
            
            # [수정됨] 이미지 크기를 50x50으로 늘림
            self.image = pygame.transform.scale(self.image, ITEM_SIZE)
            
        except FileNotFoundError:
            # 이미지가 없을 때 대체하는 네모 크기도 50x50으로 수정
            self.image = pygame.Surface(ITEM_SIZE)
            if self.type == "coffee": self.image.fill((200, 100, 50))
            else: self.image.fill((0, 255, 255))
            
        self.rect = self.image.get_rect()
        # 스폰 위치 마진도 크기에 맞춰 살짝 조정
        self.rect.x = random.randint(60, SCREEN_WIDTH - 60)
        self.rect.y = random.randint(60, SCREEN_HEIGHT - 60)
        
        self.apply_season_effect(season)

    # [신규] 시즌에 따라 아이템 회복량을 바꿔주는 함수
   # [Item 클래스 내부]
    def apply_season_effect(self, season):
        # 방학이면 회복량 2배 효과는 유지
        multiplier = 2 if season == "방학" else 1
        
        if self.type == "coffee":
            self.heal = 2 * multiplier  # (기존 2 -> 10으로 상향)
        elif self.type == "free_period":
            self.heal = 4 * multiplier  # (기존 4 -> 20으로 상향)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_type, season="평시"):
        super().__init__()
        self.type = enemy_type
        
        # --- [수정됨] 적 목표 크기를 60x60으로 설정 ---
        ENEMY_SIZE = (60, 60)
        
        try:
            if self.type == "assignment":
                self.image = pygame.image.load("assignment.png").convert_alpha()
                self.damage = 10
                self.name = "과제"
            elif self.type == "alcohol":
                self.image = pygame.image.load("alcohol.png").convert_alpha()
                self.damage = 20
                self.name = "술"

            # [수정됨] 이미지 크기를 60x60으로 늘림
            self.image = pygame.transform.scale(self.image, ENEMY_SIZE)
            
        except FileNotFoundError:
            # 대체 네모 크기도 60x60으로 수정
            self.image = pygame.Surface(ENEMY_SIZE)
            if self.type == "assignment": self.image.fill((255, 0, 0))
            else: self.image.fill((128, 0, 128))

        self.rect = self.image.get_rect()
        self.rect.x = random.choice([random.randint(0, 100), random.randint(SCREEN_WIDTH-160, SCREEN_WIDTH)])
        self.rect.y = random.choice([random.randint(0, 100), random.randint(SCREEN_HEIGHT-160, SCREEN_HEIGHT)])

        self.base_speed = random.choice([3, 4])
        self.dir_x = random.choice([-1, 1])
        self.dir_y = random.choice([-1, 1])
        
        self.speed_x = self.base_speed * self.dir_x
        self.speed_y = self.base_speed * self.dir_y
        
        self.apply_season_effect(season)

    # [신규] 시즌에 따라 몬스터 속도를 바꿔주는 함수
    def apply_season_effect(self, season):
        speed_mult = 1.5 if season == "시험기간" else (0.5 if season == "방학" else 1.0)
        
        current_sign_x = 1 if self.speed_x > 0 else -1
        current_sign_y = 1 if self.speed_y > 0 else -1
        
        new_speed = max(1, int(self.base_speed * speed_mult)) 
        
        self.speed_x = new_speed * current_sign_x
        self.speed_y = new_speed * current_sign_y

    def update(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
        
        # [수정됨] X축 모서리 끼임 방지 완벽 처리
        if self.rect.left <= 0:
            self.rect.left = 0           # 벽 밖으로 나갔다면 강제로 벽에 딱 붙임!
            self.speed_x *= -1           # 그리고 방향을 반전
        elif self.rect.right >= SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            self.speed_x *= -1

        # [수정됨] Y축 모서리 끼임 방지 완벽 처리
        if self.rect.top <= 0:
            self.rect.top = 0
            self.speed_y *= -1
        elif self.rect.bottom >= SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT
            self.speed_y *= -1

# ==========================================
# 3. 메인 게임 매니저
# ==========================================
class GameManager:
    def __init__(self):
        pygame.init()
        # 사운드 믹서 초기화
        pygame.mixer.init()
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("내 학점 구하기 (Save My GPA)")
        self.clock = pygame.time.Clock()
        
        # 폰트 설정
        self.font_title = pygame.font.SysFont("malgungothic", 60, bold=True)
        self.font_main = pygame.font.SysFont("malgungothic", 40)
        self.font_sub = pygame.font.SysFont("malgungothic", 24)
        self.font_float = pygame.font.SysFont("malgungothic", 20, bold=True)
        
        # 사운드 파일 불러오기
        try:
            self.snd_item = pygame.mixer.Sound("item.wav")
            self.snd_hit = pygame.mixer.Sound("hit.wav")
            self.snd_levelup = pygame.mixer.Sound("levelup.wav")
            self.snd_graduate = pygame.mixer.Sound("graduate.wav")
            
            self.snd_item.set_volume(0.5)
            self.snd_hit.set_volume(0.5)
        except:
            print("사운드 파일을 찾을 수 없어 무음으로 진행합니다.")
            self.snd_item = self.snd_hit = self.snd_levelup = self.snd_graduate = None
       # --- [수정됨] 배경 & 타이틀 이미지 로드 ---
        try:
            self.bg_normal = pygame.image.load("bg_normal.png").convert()
            self.bg_exam = pygame.image.load("bg_exam.png").convert()
            self.bg_vacation = pygame.image.load("bg_vacation.png").convert() # [신규] 방학 배경
            
            self.bg_normal = pygame.transform.scale(self.bg_normal, (SCREEN_WIDTH, SCREEN_HEIGHT))
            self.bg_exam = pygame.transform.scale(self.bg_exam, (SCREEN_WIDTH, SCREEN_HEIGHT))
            self.bg_vacation = pygame.transform.scale(self.bg_vacation, (SCREEN_WIDTH, SCREEN_HEIGHT))
            
            # [신규] 타이틀 로고 이미지 (스타듀밸리 감성!)
            self.title_logo = pygame.image.load("title_logo.png").convert_alpha()
            # 로고 크기가 너무 크거나 작으면 여기서 숫자를 조절하세요 (가로, 세로)
            self.title_logo = pygame.transform.scale(self.title_logo, (500, 200)) 
            
        except FileNotFoundError:
            print("일부 배경/타이틀 이미지를 찾을 수 없습니다.")
            self.bg_normal = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); self.bg_normal.fill(WHITE)
            self.bg_exam = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); self.bg_exam.fill(RED)
            self.bg_vacation = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); self.bg_vacation.fill(GREEN)
            self.title_logo = None
        # -------------------------------------
        # -------------------------------------    
        
        self.data_manager = DataManager(FILE_NAME)
        self.leaderboard = self.data_manager.load_scores()
        
        self.state = "START"
        self.running = True

        # ===== [아까 지워졌던 필수 바구니들 복구 완료!] =====
        self.all_sprites = pygame.sprite.Group()
        self.items = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player = None

        self.semesters = ["1학년 1학기", "1학년 2학기", "2학년 1학기", "2학년 2학기",
                          "3학년 1학기", "3학년 2학기", "4학년 1학기", "4학년 2학기"]
        self.current_idx = 0
        self.season = "평시"
        self.stage_duration = 20000 
        self.stage_start_time = 0
        self.input_name = ""
        self.play_bgm("bgm_main.wav")
        # =================================================
        # --- [신규] 설명서(Help) UI용 이미지 불러오기 ---
        UI_SIZE = (40, 40)
        try:
            self.ui_coffee = pygame.transform.scale(pygame.image.load("coffee.png").convert_alpha(), UI_SIZE)
            self.ui_bed = pygame.transform.scale(pygame.image.load("bed.png").convert_alpha(), UI_SIZE)
            self.ui_assign = pygame.transform.scale(pygame.image.load("assignment.png").convert_alpha(), UI_SIZE)
            self.ui_alcohol = pygame.transform.scale(pygame.image.load("alcohol.png").convert_alpha(), UI_SIZE)
        except:
            # 이미지 없을 때 대비용 더미 네모
            self.ui_coffee = pygame.Surface(UI_SIZE); self.ui_coffee.fill((200,100,50))
            self.ui_bed = pygame.Surface(UI_SIZE); self.ui_bed.fill((0,255,255))
            self.ui_assign = pygame.Surface(UI_SIZE); self.ui_assign.fill((255,0,0))
            self.ui_alcohol = pygame.Surface(UI_SIZE); self.ui_alcohol.fill((128,0,128))
        # ----------------------------------------------
        # --- [수정됨] 조작키 이미지 로드 (이동 빼고 크기 업그레이드!) ---
       # --- [수정됨] 조작키 이미지 로드 (모든 키 높이 60으로 통일!) ---
        ARROW_SIZE = (30, 30) 
        SQUARE_SIZE = (60, 60)
        
        try:
            self.ui_up = pygame.transform.scale(pygame.image.load("up.png").convert_alpha(), ARROW_SIZE)
            self.ui_down = pygame.transform.scale(pygame.image.load("down.png").convert_alpha(), ARROW_SIZE)
            self.ui_left = pygame.transform.scale(pygame.image.load("left.png").convert_alpha(), ARROW_SIZE)
            self.ui_right = pygame.transform.scale(pygame.image.load("right.png").convert_alpha(), ARROW_SIZE)
            
            # [수정됨] 스페이스바와 엔터도 높이를 60으로 맞추고 가로도 대폭 확장!
            self.ui_space = pygame.transform.scale(pygame.image.load("space.png").convert_alpha(), (160, 60))
            self.ui_enter = pygame.transform.scale(pygame.image.load("enter.png").convert_alpha(), (120, 60))
            self.ui_h = pygame.transform.scale(pygame.image.load("h.png").convert_alpha(), SQUARE_SIZE)
            self.ui_esc = pygame.transform.scale(pygame.image.load("esc.png").convert_alpha(), SQUARE_SIZE)
        except:
            print("키보드 이미지가 없어 기본 회색 네모로 대체합니다.")
            self.ui_up = self.ui_down = self.ui_left = self.ui_right = pygame.Surface(ARROW_SIZE)
            self.ui_up.fill((200,200,200))
            self.ui_space = pygame.Surface((160, 60)); self.ui_space.fill((200,200,200))
            self.ui_enter = pygame.Surface((120, 60)); self.ui_enter.fill((200,200,200))
            self.ui_h = pygame.Surface(SQUARE_SIZE); self.ui_h.fill((200,200,200))
            self.ui_esc = pygame.Surface(SQUARE_SIZE); self.ui_esc.fill((200,200,200))
        # ----------------------------------------------------
        # ----------------------------------------------------
        # ----------------------------------------------------

    def start_new_game(self):
        self.current_idx = 0
        self.input_name = ""
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.setup_stage()
        
        self.play_bgm("bgm_normal.wav")

    def setup_stage(self):
        self.all_sprites.empty()
        self.items.empty()
        self.enemies.empty()
        
        self.all_sprites.add(self.player)

        r = random.random()
        if r < 0.25: self.season = "시험기간"
        elif r < 0.50: self.season = "방학"
        else: self.season = "평시"

        self.stage_start_time = pygame.time.get_ticks()

        for _ in range(5): self.spawn_item()
        for _ in range(4): self.spawn_enemy()
        
        # [신규] 사운드 재생 함수
    def play_sound(self, sound_obj):
        if sound_obj: # 사운드 파일이 정상적으로 로드되었을 때만 재생
            sound_obj.play()
            
    # [신규] 배경음악 재생 함수
    def play_bgm(self, file_name):
        try:
            pygame.mixer.music.load(file_name)
            pygame.mixer.music.play(-1) # -1을 넣으면 노래가 안 끊기고 무한 반복됩니다!
        except:
            print(f"{file_name} 배경음악 파일을 찾을 수 없습니다.")        

    def spawn_item(self):
        item = Item(random.choice(["coffee", "free_period"]), self.season)
        self.all_sprites.add(item)
        self.items.add(item)

    def spawn_enemy(self):
        enemy = Enemy(random.choice(["assignment", "alcohol"]), self.season)
        self.all_sprites.add(enemy)
        self.enemies.add(enemy)

    def spawn_floating_text(self, x, y, text, color):
        ft = FloatingText(x, y, text, color, self.font_float)
        self.all_sprites.add(ft)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            if event.type == pygame.KEYDOWN:
                if self.state == "START":
                    if event.key == pygame.K_SPACE:
                        self.start_new_game()
                        self.state = "PLAY"
                    # [신규] H키를 누르면 설명서(HELP) 창으로 이동!
                    elif event.key == pygame.K_h:
                        self.state = "HELP"
                        
                elif self.state == "HELP":
                # ESC나 H를 누르면 다시 메인(START) 화면으로 돌아감
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_h:
                        self.play_sound(self.snd_levelup)
                        self.state = "START"
                # [수정됨] 스페이스바를 누르면 즉시 게임을 시작함!
                    elif event.key == pygame.K_SPACE:
                        self.play_sound(self.snd_levelup) # 시작 효과음
                        self.start_new_game()       
                        self.state = "PLAY"        
                elif self.state == "PLAY":
                    if event.key == pygame.K_k:
                        print("디버그: 치트키 사용 - 결과 입력 창으로 이동합니다.")
                        self.state = "RESULT_INPUT"        
                        
                elif self.state == "RESULT_INPUT":
                    if event.key == pygame.K_RETURN and len(self.input_name) > 0:
                        is_grad = self.player.gpa > 0 
                        self.data_manager.save_score(self.input_name, self.player.gpa, is_grad)
                        self.leaderboard = self.data_manager.load_scores()
                        self.state = "START"
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_name = self.input_name[:-1]
                    else:
                        if len(self.input_name) < 10 and event.unicode.isprintable():
                            self.input_name += event.unicode
                            
                elif self.state == "LEADERBOARD":
                    if event.key == pygame.K_SPACE:
                        self.state = "START"

    def update(self):
        if self.state == "PLAY":
            self.all_sprites.update()
            
            # --- [신규] 제적(엔딩1) 조건 달성 시 BGM 변경 ---
            # (학점이 0점 이하로 떨어져서 게임오버 되는 조건이라고 가정)
            if self.player.gpa <= 0.0:
                self.play_bgm("bgm_gameover.wav")
                self.state = "RESULT_INPUT" # 혹은 회원님이 지정한 게임오버 상태
                return
            # -----------------------------------------------

            # --- [수정됨] 현실 고증 반영 타임라인 시스템 ---
            elapsed = pygame.time.get_ticks() - self.stage_start_time
            
            # 현재 학기가 1학기(인덱스 0, 2, 4, 6)인지 2학기(인덱스 1, 3, 5, 7)인지 판별
            is_second_semester = (self.current_idx % 2 == 1)
            
            # 1학기는 20초(평시->시험) 후 종료, 2학기는 30초(평시->시험->방학) 후 종료
            max_duration = 30000 if is_second_semester else 20000

            # 학기 종료 판정
            if elapsed >= max_duration:
                self.current_idx += 1
                if self.current_idx >= len(self.semesters):
                    self.play_sound(self.snd_graduate)
                    self.state = "RESULT_INPUT"
                    return
                
                self.play_sound(self.snd_levelup)
                self.setup_stage()
                self.play_bgm("bgm_normal.wav")
                return
                
            # 시간 경과에 따른 시즌 변화
            if elapsed < 10000:
                new_season = "평시"
            elif elapsed < 20000:
                new_season = "시험기간"
            else:
                new_season = "방학" # 2학기에만 20초 이후 시간이 존재하므로 자연스럽게 발동

            # 시즌이 바뀌는 순간 몬스터/아이템 속성 업데이트
            if self.season != new_season:
                self.season = new_season
                for enemy in self.enemies: enemy.apply_season_effect(self.season)
                for item in self.items: item.apply_season_effect(self.season)
                
                # 상황에 맞는 BGM 틀어주기
                if self.season == "평시": self.play_bgm("bgm_normal.wav")
                elif self.season == "시험기간": self.play_bgm("bgm_exam.wav")
                elif self.season == "방학": self.play_bgm("bgm_vacation.wav")
            # ----------------------------------------------------
                    
            # ----------------------------------------
            
            # 아이템 획득
            item_hits = pygame.sprite.spritecollide(self.player, self.items, True)
            for hit in item_hits:
                self.play_sound(self.snd_item)
                self.player.mental += hit.heal
                self.spawn_floating_text(self.player.rect.centerx, self.player.rect.top, f"+{hit.heal} {hit.name}", CYAN)
                self.spawn_item() 

            # 적 충돌
            enemy_hits = pygame.sprite.spritecollide(self.player, self.enemies, True)
            for hit in enemy_hits:
                self.play_sound(self.snd_hit)
                self.player.mental -= hit.damage
                self.spawn_floating_text(self.player.rect.centerx, self.player.rect.top, f"-{hit.damage} {hit.name}", RED)
                self.spawn_enemy() 

            # 멘탈 게이지 학점 반영
            if self.player.mental >= 100:
                self.player.gpa += 0.5   
                self.player.mental = 50
                self.spawn_floating_text(self.player.rect.centerx, self.player.rect.top - 20, "학점 떡상! (+0.5)", GOLD)
            elif self.player.mental <= 0:
                self.player.gpa -= 0.5   
                self.player.mental = 50  
                self.spawn_floating_text(self.player.rect.centerx, self.player.rect.top - 20, "학사경고! (-0.5)", RED)

            if self.player.gpa > 4.5: self.player.gpa = 4.5
            if self.player.gpa <= 0.0:
                self.player.gpa = 0.0
                self.state = "RESULT_INPUT"

           # 아이템 획득
            item_hits = pygame.sprite.spritecollide(self.player, self.items, True)
            for hit in item_hits:
                self.player.mental += hit.heal
                # [수정됨] 글자 색상을 CYAN으로 변경해서 눈에 확 띄게 만듭니다.
                self.spawn_floating_text(self.player.rect.centerx, self.player.rect.top, f"+{hit.heal} {hit.name}", CYAN)
                self.spawn_item() 

            # 적 충돌
            enemy_hits = pygame.sprite.spritecollide(self.player, self.enemies, True)
            for hit in enemy_hits:
                self.player.mental -= hit.damage
                # [수정됨] 에러가 나지 않도록 새롭게 정의한 RED 사용
                self.spawn_floating_text(self.player.rect.centerx, self.player.rect.top, f"-{hit.damage} {hit.name}", RED)
                self.spawn_enemy()

            # 멘탈 게이지 학점 반영
            if self.player.mental >= 100:
                self.player.gpa += 0.5   
                self.player.mental = 50
                self.spawn_floating_text(self.player.rect.centerx, self.player.rect.top - 20, "학점 떡상! (+0.5)", GOLD)
            elif self.player.mental <= 0:
                self.player.gpa -= 0.5   
                self.player.mental = 50  
                self.spawn_floating_text(self.player.rect.centerx, self.player.rect.top - 20, "학사경고! (-0.5)", RED)

            if self.player.gpa > 4.5: self.player.gpa = 4.5
            if self.player.gpa <= 0.0:
                self.player.gpa = 0.0
                self.state = "RESULT_INPUT"    

    def draw(self):
        self.screen.fill(BLACK)

        if self.state == "START":
            self.draw_start_screen()
        elif self.state == "PLAY":
            self.draw_game_screen()
        elif self.state == "RESULT_INPUT":
            self.draw_result_screen()
       # [수정됨] HELP 상태일 때, 시작 화면을 먼저 그리고 그 위에 팝업창을 덮어씌웁니다!
        elif self.state == "HELP":
            self.draw_start_screen() # 1. 뒷배경으로 파란 시작 화면을 먼저 깐다
            self.draw_help_screen()  # 2. 그 위에 반투명한 설명서 창을 얹는다

        pygame.display.flip()

    def draw_start_screen(self):
        # 1. 배경으로 '평시(낮)' 이미지를 쫙 깝니다.
        self.screen.blit(self.bg_normal, (0, 0))
        
        # 2. 배경이 너무 밝으면 글씨가 안 보일 수 있으니, 반투명한 어두운 필터를 살짝 씌웁니다.
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(100) # 0~255 사이 조절 (낮을수록 투명함)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # 3. 텍스트 대신 예쁜 '타이틀 로고 이미지' 띄우기
        if self.title_logo:
            logo_x = SCREEN_WIDTH // 2 - self.title_logo.get_width() // 2
            self.screen.blit(self.title_logo, (logo_x, 50))
        else:
            # 혹시 로고 이미지가 없으면 기존 텍스트로 대체
            title_text = self.font_title.render("내 학점 구하기", True, GOLD)
            self.screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 80))

        # 4. 안내 문구 (로고 이미지 아래로 넉넉하게 위치 조정)
        start_text = self.font_sub.render("Press SPACE to Start", True, WHITE)
        help_text = self.font_sub.render("Press 'H' for How to Play", True, CYAN)
        
        self.screen.blit(start_text, (SCREEN_WIDTH//2 - start_text.get_width()//2, 270))
        self.screen.blit(help_text, (SCREEN_WIDTH//2 - help_text.get_width()//2, 320))

        # 5. 명예의 전당 (위치 살짝 아래로 조정)
        board_y = 390
        board_title = self.font_main.render("--- 역대 명예의 전당 ---", True, GRAY)
        self.screen.blit(board_title, (SCREEN_WIDTH//2 - board_title.get_width()//2, board_y))
        
        for i, record in enumerate(self.leaderboard[:4]): # 칸이 좁아져서 4위까지만!
            text = f"{i+1}위. {record['name']} | 학점: {record['gpa']:.1f} ({record['status']})"
            record_text = self.font_sub.render(text, True, WHITE)
            self.screen.blit(record_text, (SCREEN_WIDTH//2 - 150, board_y + 40 + (i * 30)))


   # [신규] 게임 설명서(How To Play) 그리기 함수
    def draw_help_screen(self):
        # 1. 반투명한 검은색 배경 깔기
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # --- [수정됨] 2. 팝업창 세로 길이를 520 -> 540으로 연장 ---
        popup_rect = pygame.Rect(40, 30, 720, 540) 
        pygame.draw.rect(self.screen, WHITE, popup_rect, border_radius=15)
        pygame.draw.rect(self.screen, (255, 180, 0), popup_rect, 6, border_radius=15)
        
        # 3. 메인 타이틀
        title = self.font_title.render("HOW TO PLAY", True, (255, 120, 0))
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 45))
        
        # =========================================================
        # [섹션 1: 방법]
        # =========================================================
        pygame.draw.rect(self.screen, (255, 150, 0), (70, 120, 70, 30), border_radius=5)
        self.screen.blit(self.font_sub.render("방법", True, WHITE), (83, 120))
        
        desc1 = self.font_sub.render("다가오는 과제와 술을 피해 학점(GPA)을 사수하세요!", True, BLACK)
        desc2 = self.font_sub.render("멘탈이 0이 되면 학점이 깎입니다. 무사히 졸업하세요!", True, BLACK)
        self.screen.blit(desc1, (150, 120))
        self.screen.blit(desc2, (150, 150))

        # =========================================================
        # [섹션 2: 아이템]
        # =========================================================
        pygame.draw.rect(self.screen, (255, 150, 0), (70, 210, 90, 30), border_radius=5)
        self.screen.blit(self.font_sub.render("아이템", True, WHITE), (80, 210))
        
        self.screen.blit(self.ui_coffee, (100, 260))
        self.screen.blit(self.font_sub.render("커피: 멘탈 +2 (방학 2배)", True, BLUE), (150, 265))
        
        self.screen.blit(self.ui_bed, (100, 320))
        self.screen.blit(self.font_sub.render("공강: 멘탈 +4 (방학 2배)", True, BLUE), (150, 325))

        self.screen.blit(self.ui_assign, (430, 260))
        self.screen.blit(self.font_sub.render("과제: 멘탈 -10", True, RED), (480, 265))
        
        self.screen.blit(self.ui_alcohol, (430, 320))
        self.screen.blit(self.font_sub.render("술: 멘탈 -20", True, RED), (480, 325))

        # =========================================================
        # =========================================================
        # [섹션 3: 조작]
        # =========================================================
        pygame.draw.rect(self.screen, (255, 150, 0), (70, 385, 70, 30), border_radius=5)
        self.screen.blit(self.font_sub.render("조작", True, WHITE), (83, 385))
        
        # 1. 방향키 (왼쪽으로 살짝 당김)
        arr_x, arr_y = 80, 420  # 100 -> 80으로 수정
        self.screen.blit(self.ui_up, (arr_x + 32, arr_y))
        self.screen.blit(self.ui_left, (arr_x, arr_y + 32))
        self.screen.blit(self.ui_down, (arr_x + 32, arr_y + 32))
        self.screen.blit(self.ui_right, (arr_x + 64, arr_y + 32))
        self.screen.blit(self.font_sub.render("이동", True, BLACK), (arr_x + 105, arr_y + 20))
        
        # 2. 스페이스바 & 엔터키 (오른쪽으로 시원하게 밀어줌)
        self.screen.blit(self.ui_space, (280, 415)) # 240 -> 280으로 수정
        self.screen.blit(self.font_sub.render("게임 시작", True, BLACK), (450, 430)) 
        
        self.screen.blit(self.ui_enter, (280, 485)) 
        self.screen.blit(self.font_sub.render("입력 완료", True, BLACK), (450, 500)) 
        
        # 3. H키 & ESC키 (끝쪽으로 더 밀어서 밸런스 맞춤)
        self.screen.blit(self.ui_h, (570, 415)) # 530 -> 570으로 수정
        self.screen.blit(self.font_sub.render("도움말", True, BLACK), (640, 430)) 
        
        self.screen.blit(self.ui_esc, (570, 485))
        self.screen.blit(self.font_sub.render("창 닫기", True, BLACK), (640, 500))



    def draw_game_screen(self):
        # --- [수정됨] 3계절 배경화면 완벽 적용 ---
        if self.season == "시험기간":
            self.screen.blit(self.bg_exam, (0, 0)) 
        elif self.season == "방학":
            self.screen.blit(self.bg_vacation, (0, 0)) # 방학 배경!
        else:
            self.screen.blit(self.bg_normal, (0, 0))
        # ----------------------------------------

        self.all_sprites.draw(self.screen)
        # (이하 생략: 타이머, 게이지 그리는 코드 그대로 유지)
        
        # --- [수정됨] 1/2학기에 맞춰 타이머 최대치 자동 조절 ---
        is_second_semester = (self.current_idx % 2 == 1)
        max_duration = 30000 if is_second_semester else 20000
        
        elapsed = pygame.time.get_ticks() - self.stage_start_time
        time_left = max(0, (max_duration - elapsed) // 1000)
        # --------------------------------------------------
        
        ui_color = WHITE if self.season == "시험기간" else BLACK
        
        # 게이지 바 시각화
        pygame.draw.rect(self.screen, BLACK, (10, 45, 204, 24), 2)
        pygame.draw.rect(self.screen, BLUE, (12, 47, self.player.mental * 2, 20))
        
        ui_text = self.font_sub.render(f"GPA: {self.player.gpa:.1f} | Mental:", True, ui_color)
        info_text = self.font_sub.render(f"[{self.semesters[self.current_idx]}] {self.season} - 남은 시간: {time_left}초", True, ui_color)
        
        self.screen.blit(ui_text, (10, 10))
        self.screen.blit(info_text, (10, 80))
        

    def draw_result_screen(self):
        self.screen.fill(BLACK)
        msg = "졸업을 축하합니다!" if self.player.gpa > 0 else "제적되었습니다..."
        color = GOLD if self.player.gpa > 0 else RED
            
        result_text = self.font_title.render(msg, True, color)
        score_text = self.font_main.render(f"최종 학점: {self.player.gpa:.1f}", True, WHITE)
        
        input_prompt = self.font_sub.render("이니셜 3글자를 입력하고 ENTER를 누르세요:", True, GRAY)
        name_text = self.font_title.render(self.input_name + "_", True, WHITE)
        
        self.screen.blit(result_text, (SCREEN_WIDTH//2 - result_text.get_width()//2, 100))
        self.screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 200))
        self.screen.blit(input_prompt, (SCREEN_WIDTH//2 - input_prompt.get_width()//2, 350))
        self.screen.blit(name_text, (SCREEN_WIDTH//2 - name_text.get_width()//2, 400))

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = GameManager()
    game.run()