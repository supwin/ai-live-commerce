# app/utils/file_handler.py
"""
File Handler Utility for AI Live Commerce Platform
Handles file uploads, validation, and management for images, videos, and audio
"""

import os
import hashlib
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import aiofiles
from fastapi import UploadFile, HTTPException
import mimetypes
from PIL import Image
import json
from datetime import datetime

class FileHandler:
    """Comprehensive file handling utility"""
    
    def __init__(self):
        # Base directories
        self.upload_dir = Path("frontend/uploads")
        self.static_dir = Path("frontend/static")
        
        # Subdirectories
        self.image_dir = self.upload_dir / "images"
        self.video_dir = self.upload_dir / "videos"
        self.audio_dir = self.static_dir / "audio"
        self.thumbnail_dir = self.upload_dir / "thumbnails"
        
        # Create directories
        self._ensure_directories()
        
        # File size limits (in bytes)
        self.max_image_size = 10 * 1024 * 1024  # 10MB
        self.max_video_size = 100 * 1024 * 1024  # 100MB
        self.max_audio_size = 10 * 1024 * 1024   # 10MB
        
        # Allowed file extensions
        self.allowed_image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        self.allowed_video_exts = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'}
        self.allowed_audio_exts = {'.mp3', '.wav', '.ogg', '.m4a'}
        
        # MIME type mapping
        self.mime_types = {
            'image': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
            'video': ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo', 'video/webm'],
            'audio': ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4']
        }
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            self.upload_dir,
            self.image_dir,
            self.video_dir,
            self.audio_dir,
            self.thumbnail_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _generate_filename(self, original_filename: str, file_type: str = "file") -> str:
        """Generate unique filename with timestamp and UUID"""
        # Get file extension
        ext = Path(original_filename).suffix.lower()
        
        # Generate unique identifier
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        # Clean original name (remove extension and special chars)
        clean_name = Path(original_filename).stem
        clean_name = "".join(c for c in clean_name if c.isalnum() or c in (' ', '-', '_')).strip()
        clean_name = clean_name.replace(' ', '_')[:30]  # Limit length
        
        # Construct filename
        if clean_name:
            filename = f"{file_type}_{timestamp}_{clean_name}_{unique_id}{ext}"
        else:
            filename = f"{file_type}_{timestamp}_{unique_id}{ext}"
        
        return filename
    
    def _validate_file(self, file: UploadFile, file_type: str) -> Dict[str, Any]:
        """Validate uploaded file"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "file_info": {}
        }
        
        # Check file extension
        ext = Path(file.filename).suffix.lower()
        
        if file_type == "image":
            allowed_exts = self.allowed_image_exts
            max_size = self.max_image_size
            allowed_mimes = self.mime_types['image']
        elif file_type == "video":
            allowed_exts = self.allowed_video_exts
            max_size = self.max_video_size
            allowed_mimes = self.mime_types['video']
        elif file_type == "audio":
            allowed_exts = self.allowed_audio_exts
            max_size = self.max_audio_size
            allowed_mimes = self.mime_types['audio']
        else:
            validation["valid"] = False
            validation["errors"].append(f"Unsupported file type: {file_type}")
            return validation
        
        # Validate extension
        if ext not in allowed_exts:
            validation["valid"] = False
            validation["errors"].append(f"File extension {ext} not allowed for {file_type}")
        
        # Validate MIME type
        if file.content_type not in allowed_mimes:
            validation["warnings"].append(f"MIME type {file.content_type} may not be supported")
        
        # File info
        validation["file_info"] = {
            "original_name": file.filename,
            "extension": ext,
            "content_type": file.content_type,
            "size": file.size if hasattr(file, 'size') else None
        }
        
        return validation
    
    async def upload_image(
        self, 
        file: UploadFile, 
        product_id: Optional[int] = None,
        resize: bool = True,
        max_width: int = 1200,
        max_height: int = 1200
    ) -> Dict[str, Any]:
        """Upload and process image file"""
        try:
            # Validate file
            validation = self._validate_file(file, "image")
            if not validation["valid"]:
                raise HTTPException(status_code=400, detail=validation["errors"])
            
            # Generate filename
            filename = self._generate_filename(file.filename, "img")
            file_path = self.image_dir / filename
            
            # Read file content
            content = await file.read()
            
            # Check file size
            if len(content) > self.max_image_size:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Image file too large. Maximum size: {self.max_image_size / 1024 / 1024:.1f}MB"
                )
            
            # Save original file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            # Process image if needed
            processed_info = {}
            if resize:
                processed_info = await self._process_image(file_path, max_width, max_height)
            
            # Get image dimensions
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
                    format_name = img.format
            except Exception as e:
                width, height, format_name = None, None, None
                print(f"Warning: Could not get image dimensions: {e}")
            
            result = {
                "success": True,
                "filename": filename,
                "file_path": str(file_path),
                "web_url": f"/uploads/images/{filename}",
                "file_size": len(content),
                "file_size_mb": round(len(content) / 1024 / 1024, 2),
                "dimensions": {
                    "width": width,
                    "height": height,
                    "format": format_name
                },
                "original_name": file.filename,
                "content_type": file.content_type,
                "upload_timestamp": datetime.now().isoformat(),
                "product_id": product_id
            }
            
            if processed_info:
                result["processed"] = processed_info
            
            if validation["warnings"]:
                result["warnings"] = validation["warnings"]
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            # Clean up file if it was created
            if 'file_path' in locals() and file_path.exists():
                try:
                    file_path.unlink()
                except:
                    pass
            
            raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")
    
    async def _process_image(
        self, 
        file_path: Path, 
        max_width: int, 
        max_height: int
    ) -> Dict[str, Any]:
        """Process image: resize, optimize, create thumbnail"""
        try:
            with Image.open(file_path) as img:
                original_size = img.size
                
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # Resize if needed
                if img.size[0] > max_width or img.size[1] > max_height:
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                    img.save(file_path, 'JPEG', quality=85, optimize=True)
                
                # Create thumbnail
                thumbnail_filename = f"thumb_{file_path.name}"
                thumbnail_path = self.thumbnail_dir / thumbnail_filename
                
                thumb_img = img.copy()
                thumb_img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                thumb_img.save(thumbnail_path, 'JPEG', quality=80)
                
                return {
                    "resized": True,
                    "original_size": original_size,
                    "new_size": img.size,
                    "thumbnail": {
                        "filename": thumbnail_filename,
                        "path": str(thumbnail_path),
                        "web_url": f"/uploads/thumbnails/{thumbnail_filename}"
                    }
                }
                
        except Exception as e:
            print(f"Warning: Image processing failed: {e}")
            return {"resized": False, "error": str(e)}
    
    async def upload_video(
        self, 
        file: UploadFile, 
        product_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Upload video file"""
        try:
            # Validate file
            validation = self._validate_file(file, "video")
            if not validation["valid"]:
                raise HTTPException(status_code=400, detail=validation["errors"])
            
            # Generate filename
            filename = self._generate_filename(file.filename, "video")
            file_path = self.video_dir / filename
            
            # Read and save file in chunks to handle large files
            file_size = 0
            async with aiofiles.open(file_path, 'wb') as f:
                while chunk := await file.read(8192):  # 8KB chunks
                    file_size += len(chunk)
                    
                    # Check size limit during upload
                    if file_size > self.max_video_size:
                        # Clean up partial file
                        await f.close()
                        file_path.unlink()
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Video file too large. Maximum size: {self.max_video_size / 1024 / 1024:.1f}MB"
                        )
                    
                    await f.write(chunk)
            
            # Get video info (basic)
            video_info = await self._get_video_info(file_path)
            
            result = {
                "success": True,
                "filename": filename,
                "file_path": str(file_path),
                "web_url": f"/uploads/videos/{filename}",
                "file_size": file_size,
                "file_size_mb": round(file_size / 1024 / 1024, 2),
                "original_name": file.filename,
                "content_type": file.content_type,
                "upload_timestamp": datetime.now().isoformat(),
                "product_id": product_id,
                "video_info": video_info
            }
            
            if validation["warnings"]:
                result["warnings"] = validation["warnings"]
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            # Clean up file if it was created
            if 'file_path' in locals() and file_path.exists():
                try:
                    file_path.unlink()
                except:
                    pass
            
            raise HTTPException(status_code=500, detail=f"Error uploading video: {str(e)}")
    
    async def _get_video_info(self, file_path: Path) -> Dict[str, Any]:
        """Get basic video information"""
        try:
            # For now, return basic file info
            # In production, you might want to use ffprobe or similar
            stat = file_path.stat()
            
            return {
                "duration": None,  # Would need ffprobe
                "resolution": None,  # Would need ffprobe
                "codec": None,  # Would need ffprobe
                "bitrate": None,  # Would need ffprobe
                "file_created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "file_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        except Exception as e:
            return {"error": f"Could not get video info: {e}"}
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file safely"""
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                path.unlink()
                print(f"🗑️ Deleted file: {file_path}")
                return True
            return False
        except Exception as e:
            print(f"❌ Error deleting file {file_path}: {e}")
            return False
    
    def delete_product_files(self, product_id: int) -> Dict[str, int]:
        """Delete all files associated with a product"""
        deleted_counts = {
            "images": 0,
            "videos": 0,
            "thumbnails": 0
        }
        
        try:
            # Find files by product ID (you'd need to implement a file registry)
            # For now, this is a placeholder
            print(f"🗑️ Would delete files for product {product_id}")
            
            return deleted_counts
            
        except Exception as e:
            print(f"❌ Error deleting product files: {e}")
            return deleted_counts
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get information about a file"""
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            stat = path.stat()
            
            return {
                "filename": path.name,
                "file_path": str(path),
                "file_size": stat.st_size,
                "file_size_mb": round(stat.st_size / 1024 / 1024, 2),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "extension": path.suffix.lower(),
                "exists": True
            }
            
        except Exception as e:
            return {"error": f"Could not get file info: {e}", "exists": False}
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            stats = {
                "directories": {},
                "total_size": 0,
                "total_files": 0
            }
            
            directories = [
                ("images", self.image_dir),
                ("videos", self.video_dir),
                ("audio", self.audio_dir),
                ("thumbnails", self.thumbnail_dir)
            ]
            
            for name, directory in directories:
                if directory.exists():
                    files = list(directory.glob("*"))
                    total_size = sum(f.stat().st_size for f in files if f.is_file())
                    
                    stats["directories"][name] = {
                        "path": str(directory),
                        "file_count": len([f for f in files if f.is_file()]),
                        "total_size": total_size,
                        "total_size_mb": round(total_size / 1024 / 1024, 2)
                    }
                    
                    stats["total_size"] += total_size
                    stats["total_files"] += len([f for f in files if f.is_file()])
                else:
                    stats["directories"][name] = {
                        "path": str(directory),
                        "file_count": 0,
                        "total_size": 0,
                        "total_size_mb": 0,
                        "exists": False
                    }
            
            stats["total_size_mb"] = round(stats["total_size"] / 1024 / 1024, 2)
            stats["total_size_gb"] = round(stats["total_size"] / 1024 / 1024 / 1024, 2)
            
            return stats
            
        except Exception as e:
            return {"error": f"Could not get storage stats: {e}"}
    
    def cleanup_orphaned_files(self) -> Dict[str, int]:
        """Clean up orphaned files (files not referenced in database)"""
        # This would require database integration to check which files are still referenced
        # For now, return placeholder
        return {
            "images_deleted": 0,
            "videos_deleted": 0,
            "audio_deleted": 0,
            "thumbnails_deleted": 0
        }
    
    def validate_file_access(self, file_path: str, user_id: Optional[int] = None) -> bool:
        """Validate if user has access to a file"""
        try:
            path = Path(file_path)
            
            # Check if file exists and is in allowed directories
            allowed_dirs = [self.upload_dir, self.static_dir]
            
            for allowed_dir in allowed_dirs:
                try:
                    path.resolve().relative_to(allowed_dir.resolve())
                    return True
                except ValueError:
                    continue
            
            return False
            
        except Exception as e:
            print(f"❌ File access validation error: {e}")
            return False
    
    def get_web_url(self, file_path: str) -> Optional[str]:
        """Convert file path to web-accessible URL"""
        try:
            path = Path(file_path)
            
            # Map directories to web URLs
            if self.image_dir in path.parents or path.parent == self.image_dir:
                return f"/uploads/images/{path.name}"
            elif self.video_dir in path.parents or path.parent == self.video_dir:
                return f"/uploads/videos/{path.name}"
            elif self.audio_dir in path.parents or path.parent == self.audio_dir:
                return f"/static/audio/{path.name}"
            elif self.thumbnail_dir in path.parents or path.parent == self.thumbnail_dir:
                return f"/uploads/thumbnails/{path.name}"
            
            return None
            
        except Exception as e:
            print(f"❌ Error getting web URL: {e}")
            return None

# Global file handler instance
file_handler = FileHandler()