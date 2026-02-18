from ..utils.llm_client import LLMClient
from ..utils.file_text import extract_text_from_upload


class OcResumeService:
    def __init__(self):
        self.llm = LLMClient()

    def _extract_roles(self, source_text: str) -> list:
        system = (
            "你是角色设定解析器。请从文本中识别可能的角色/人物设定，输出严格 JSON。"
            "只返回角色列表，最多 6 个。若无法判断或只有一个角色，也要照实返回。"
        )
        user = (
            "输出 JSON schema：\n"
            "{\n"
            '  "roles": [{"name": "", "summary": ""}]\n'
            "}\n\n"
            "要求：\n"
            "1) name 为角色名或最能代表角色的称呼。\n"
            "2) summary 用一句话概括角色背景或定位（<=30字）。\n"
            "3) 若只有一个角色，roles 只包含一个对象。\n"
            "4) 若无法判断，roles 返回空数组。\n\n"
            f"文本内容：\n{source_text}\n"
        )
        try:
            data = self.llm.chat_json(
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.2,
                max_tokens=800,
                use_boost=False
            )
            roles = data.get("roles") or []
            cleaned = []
            seen = set()
            for r in roles:
                name = (r.get("name") or "").strip()
                summary = (r.get("summary") or "").strip()
                if not name or name in seen:
                    continue
                seen.add(name)
                cleaned.append({"name": name, "summary": summary[:60]})
            return cleaned[:6]
        except Exception:
            return []

    def generate_from_file(self, filename: str, content: bytes, target_role: str, target_level: str, selected_role: str = "") -> dict:
        extracted = extract_text_from_upload(filename=filename, content=content)
        source_text = (extracted.get("text") or "").strip()
        if not source_text:
            raise ValueError("无法从文件中提取文本内容，请上传可复制文本的 PDF 或 txt/md")

        source_text = source_text[:18000]

        roles = self._extract_roles(source_text)
        if roles and len(roles) > 1 and not selected_role:
            return {
                "roles": roles,
                "requires_role_select": True,
                "extracted_meta": extracted.get("meta") or {},
                "extracted_text_preview": source_text[:800]
            }

        focus_role = selected_role.strip()
        if not focus_role and len(roles) == 1:
            focus_role = roles[0].get("name") or ""

        system = (
            "你是资深简历顾问与招聘官，擅长把“原创角色(OC)设定/人物小传/战绩经历/技能清单”改写成真实可投递的职场简历。"
            "必须输出严格 JSON（不要 Markdown、不要解释），字段必须齐全且可直接用于前端简历排版。"
            "内容要求：自洽、可读、量化、避免玄幻词汇；可以把设定映射为现实经历（如军团=事业部，副本=项目）。"
        )

        role_line = f"当前只为角色：{focus_role} 生成简历，忽略其他角色内容。\n\n" if focus_role else ""
        user = (
            f"目标岗位：{target_role}\n"
            f"目标级别：{target_level}\n\n"
            f"{role_line}"
            "请根据以下上传文件内容生成一份中文简历 JSON。\n"
            "输出 JSON schema（必须严格遵守字段与类型）：\n"
            "{\n"
            '  "basics": {"name": "", "title": "", "phone": "", "email": "", "location": "", "website": "", "links": [{"label":"", "url":""}]},\n'
            '  "summary": "",\n'
            '  "skills": [{"category":"", "items":[""]}],\n'
            '  "experience": [{"company":"", "role":"", "start":"YYYY-MM", "end":"YYYY-MM/至今", "location":"", "highlights":[""]}],\n'
            '  "projects": [{"name":"", "role":"", "start":"YYYY-MM", "end":"YYYY-MM/至今", "highlights":[""], "tech":[""], "metrics":[""]}],\n'
            '  "education": [{"school":"", "major":"", "degree":"", "start":"YYYY-MM", "end":"YYYY-MM", "highlights":[""]}],\n'
            '  "awards": [""],\n'
            '  "certs": [""],\n'
            '  "portfolio": [{"name":"", "url":"", "desc":""}],\n'
            '  "tags": [""],\n'
            '  "notes": {"oc_mapping": ""}\n'
            "}\n\n"
            "规则：\n"
            "1) 允许虚构但要像真实候选人；不要出现明显违法/危险内容。\n"
            "2) 所有数组至少给 1 条（没有就给空字符串占位）。\n"
            "3) 重点突出与目标岗位相关技能与项目，项目 highlights 使用 STAR/量化。\n"
            "4) basics.phone/email 可以留空。\n\n"
            "上传文件内容：\n"
            f"{source_text}\n"
        )

        resume = self.llm.chat_json(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.3,
            max_tokens=4096,
            use_boost=False
        )

        if not isinstance(resume, dict):
            raise ValueError("简历生成失败：模型未返回 JSON 对象")

        resume.setdefault("basics", {})
        resume.setdefault("summary", "")
        resume.setdefault("skills", [{"category": "", "items": [""]}])
        resume.setdefault("experience", [{"company": "", "role": "", "start": "", "end": "", "location": "", "highlights": [""]}])
        resume.setdefault("projects", [{"name": "", "role": "", "start": "", "end": "", "highlights": [""], "tech": [""], "metrics": [""]}])
        resume.setdefault("education", [{"school": "", "major": "", "degree": "", "start": "", "end": "", "highlights": [""]}])
        resume.setdefault("awards", [""])
        resume.setdefault("certs", [""])
        resume.setdefault("portfolio", [{"name": "", "url": "", "desc": ""}])
        resume.setdefault("tags", [""])
        resume.setdefault("notes", {"oc_mapping": ""})

        return {
            "resume": resume,
            "extracted_meta": extracted.get("meta") or {},
            "extracted_text_preview": source_text[:800]
        }
