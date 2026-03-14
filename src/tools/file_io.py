import os


def read_file(file_path: str) -> str:
    """
    지정된 경로의 파일 내용을 읽어 반환합니다.

    Args:
        file_path: 읽을 파일의 경로

    Returns:
        파일 내용 문자열
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"❌ 파일을 찾을 수 없습니다: {file_path}"
    except Exception as e:
        return f"❌ 파일 읽기 중 오류 발생: {e}"


def save_file(file_path: str, content: str) -> str:
    """
    지정된 경로에 파일의 내용을 저장합니다. 디렉토리가 없으면 생성합니다.

    Args:
        file_path: 저장할 파일의 경로
        content: 파일에 쓸 내용
    
    Returns:
        파일 저장 성공 메시지
    """
    try:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ 파일이 '{file_path}'에 성공적으로 저장되었습니다."
    except Exception as e:
        return f"❌ 파일 저장 중 오류 발생: {e}"
