import uuid

from flask import request, jsonify

from . import recruit_bp
from ..config import Config
from ..services.recruit_store import RecruitStore
from ..services.company_catalog import list_companies
from ..services.recruit_chat_service import RecruitChatService
from ..services.oc_resume_service import OcResumeService
from ..utils.logger import get_logger


logger = get_logger('wannian.api.recruit')

_oc_resume_service = None
_store = None
_chat_service = None


def get_oc_resume_service():
    global _oc_resume_service
    if _oc_resume_service is None:
        _oc_resume_service = OcResumeService()
    return _oc_resume_service


def get_store():
    global _store
    if _store is None:
        _store = RecruitStore()
    return _store


def get_chat_service():
    global _chat_service
    if _chat_service is None:
        _chat_service = RecruitChatService()
    return _chat_service


@recruit_bp.route('/oc-resume/from-file', methods=['POST'])
def oc_resume_from_file():
    try:
        config_errors = Config.validate()
        if config_errors:
            return jsonify({
                "success": False,
                "error": "配置缺失",
                "details": config_errors,
                "hint": "请在项目根目录创建 .env 文件并配置 LLM_API_KEY。具体参考 .env.example 文件。"
            }), 400

        if 'file' not in request.files:
            return jsonify({"success": False, "error": "缺少上传文件字段 file"}), 400

        f = request.files['file']
        if not f or not f.filename:
            return jsonify({"success": False, "error": "上传文件为空"}), 400

        filename = f.filename
        content = f.read()
        if not content:
            return jsonify({"success": False, "error": "上传文件内容为空"}), 400
        if len(content) > 5 * 1024 * 1024:
            return jsonify({"success": False, "error": "文件过大（上限 5MB）"}), 413

        target_role = request.form.get('target_role') or request.args.get('target_role') or "不限"
        target_level = request.form.get('target_level') or request.args.get('target_level') or "不限"
        selected_role = request.form.get('selected_role') or request.args.get('selected_role') or ""

        service = get_oc_resume_service()
        result = service.generate_from_file(
            filename=filename,
            content=content,
            target_role=target_role,
            target_level=target_level,
            selected_role=selected_role
        )

        if result.get("requires_role_select"):
            return jsonify({"success": True, "data": result})

        resume_id = str(uuid.uuid4())
        result["resume_id"] = resume_id
        get_store().upsert_resume(resume_id=resume_id, resume=result.get("resume") or {})

        return jsonify({"success": True, "data": result})
    except ValueError as ve:
        logger.error(f"配置错误: {str(ve)}")
        return jsonify({
            "success": False,
            "error": str(ve),
            "hint": "请检查 .env 文件中的 LLM_API_KEY 配置"
        }), 400
    except Exception as e:
        logger.error(f"生成简历失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@recruit_bp.route('/companies', methods=['GET'])
def get_companies():
    try:
        return jsonify({"success": True, "data": list_companies()})
    except Exception as e:
        logger.error(f"获取公司列表失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@recruit_bp.route('/apply', methods=['POST'])
def apply_company():
    try:
        data = request.get_json(silent=True) or {}
        resume_id = data.get("resume_id")
        company_id = data.get("company_id")
        if not resume_id or not company_id:
            return jsonify({"success": False, "error": "缺少 resume_id 或 company_id"}), 400

        resume = get_store().get_resume(resume_id)
        if not resume:
            return jsonify({"success": False, "error": "resume_id 不存在或已过期"}), 404

        company = next((c for c in list_companies() if c["id"] == company_id), None)
        if not company:
            return jsonify({"success": False, "error": "company_id 不存在"}), 404

        app = get_store().create_application(resume_id=resume_id, company=company)
        return jsonify({"success": True, "data": app})
    except Exception as e:
        logger.error(f"投递失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@recruit_bp.route('/applications', methods=['GET'])
def list_applications():
    try:
        resume_id = request.args.get("resume_id")
        apps = get_store().list_applications(resume_id=resume_id)
        return jsonify({"success": True, "data": apps})
    except Exception as e:
        logger.error(f"获取投递记录失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@recruit_bp.route('/chat/history', methods=['GET'])
def chat_history():
    try:
        application_id = request.args.get("application_id")
        if not application_id:
            return jsonify({"success": False, "error": "缺少 application_id"}), 400
        app = get_store().get_application(application_id)
        if not app:
            return jsonify({"success": False, "error": "application_id 不存在"}), 404
        chat = get_store().get_or_create_chat(app)
        messages = get_store().list_chat_messages(application_id)
        return jsonify({"success": True, "data": {"chat": chat, "messages": messages}})
    except Exception as e:
        logger.error(f"获取聊天记录失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@recruit_bp.route('/chat/send', methods=['POST'])
def chat_send():
    try:
        config_errors = Config.validate()
        if config_errors:
            return jsonify({
                "success": False,
                "error": "配置缺失",
                "details": config_errors,
                "hint": "请在项目根目录创建 .env 文件并配置 LLM_API_KEY。具体参考 .env.example 文件。"
            }), 400

        data = request.get_json(silent=True) or {}
        application_id = data.get("application_id")
        message = (data.get("message") or "").strip()
        if not application_id or not message:
            return jsonify({"success": False, "error": "缺少 application_id 或 message"}), 400

        service = get_chat_service()
        result = service.send(application_id=application_id, user_message=message)
        return jsonify({"success": True, "data": result})
    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        logger.error(f"发送聊天失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
