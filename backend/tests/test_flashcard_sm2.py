import pytest
from datetime import datetime
from src.services.flashcard_service import FlashcardService

def test_sm2_algorithm():
    service = FlashcardService()
    
    # 1. New card, perfect rating
    ef1, interval1, rep1 = service._calculate_sm2(ease_factor=2.5, interval=0, repetitions=0, rating=5)
    assert rep1 == 1
    assert interval1 == 1
    assert ef1 == 2.6 # 2.5 + (0.1 - (0) * ...) = 2.6
    
    # 2. Second perfect rating
    ef2, interval2, rep2 = service._calculate_sm2(ease_factor=ef1, interval=interval1, repetitions=rep1, rating=5)
    assert rep2 == 2
    assert interval2 == 6
    assert ef2 == 2.7
    
    # 3. Third perfect rating
    ef3, interval3, rep3 = service._calculate_sm2(ease_factor=ef2, interval=interval2, repetitions=rep2, rating=5)
    assert rep3 == 3
    assert interval3 == 16 # round(6 * 2.7 = 16.2)
    assert ef3 == 2.8
    
    # 4. Same card, forgets it (rating falls below 3)
    ef4, interval4, rep4 = service._calculate_sm2(ease_factor=ef3, interval=interval3, repetitions=rep3, rating=1)
    assert rep4 == 0
    assert interval4 == 0
    assert ef4 < ef3 # Should decrease

    # 5. Ease factor bottom limit testing
    ef_low, _, _ = service._calculate_sm2(ease_factor=1.3, interval=0, repetitions=0, rating=0)
    assert ef_low == 1.3 # Hard floor
