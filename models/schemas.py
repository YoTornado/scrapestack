"""Pydantic data models for all platforms."""

from pydantic import BaseModel
from typing import Optional


# ── Instagram ──────────────────────────────────────────────

class InstagramVideo(BaseModel):
    video_url: str
    post_date: Optional[str] = None
    caption: Optional[str] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    views: Optional[int] = None
    duration_seconds: Optional[float] = None
    transcript: Optional[str] = None


class InstagramAccount(BaseModel):
    username: str
    followers: Optional[int] = None
    following: Optional[int] = None
    total_posts: Optional[int] = None
    engagement_rate: Optional[float] = None
    bio: Optional[str] = None


# ── TikTok ─────────────────────────────────────────────────

class TikTokVideo(BaseModel):
    video_url: str
    post_date: Optional[str] = None
    caption: Optional[str] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    views: Optional[int] = None
    duration_seconds: Optional[float] = None
    transcript: Optional[str] = None
    sounds: Optional[str] = None


class TikTokAccount(BaseModel):
    username: str
    followers: Optional[int] = None
    following: Optional[int] = None
    total_likes: Optional[int] = None
    engagement_rate: Optional[float] = None
    bio: Optional[str] = None


# ── YouTube ────────────────────────────────────────────────

class YouTubeVideo(BaseModel):
    video_url: str
    title: Optional[str] = None
    publish_date: Optional[str] = None
    description: Optional[str] = None
    views: Optional[int] = None
    likes: Optional[int] = None
    comments_count: Optional[int] = None
    duration: Optional[str] = None
    transcript: Optional[str] = None
    tags: Optional[list[str]] = None


# ── LinkedIn ───────────────────────────────────────────────

class LinkedInProfile(BaseModel):
    name: Optional[str] = None
    headline: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    current_school: Optional[str] = None
    major: Optional[str] = None
    graduation_year: Optional[str] = None
    experience: Optional[list[dict]] = None
    honors_awards: Optional[list[str]] = None
    projects: Optional[list[dict]] = None
    skills: Optional[list[str]] = None
    profile_url: Optional[str] = None
