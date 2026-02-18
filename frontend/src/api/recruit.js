import service from './index'

export const generateOcResumeFromFile = (file, options = {}) => {
  const form = new FormData()
  form.append('file', file)
  if (options.target_role) form.append('target_role', options.target_role)
  if (options.target_level) form.append('target_level', options.target_level)
  if (options.selected_role) form.append('selected_role', options.selected_role)
  return service({
    url: '/api/recruit/oc-resume/from-file',
    method: 'post',
    data: form
  })
}

export const listCompanies = () => {
  return service({
    url: '/api/recruit/companies',
    method: 'get'
  })
}

export const applyToCompany = ({ resume_id, company_id }) => {
  return service({
    url: '/api/recruit/apply',
    method: 'post',
    data: { resume_id, company_id }
  })
}

export const listApplications = ({ resume_id } = {}) => {
  return service({
    url: '/api/recruit/applications',
    method: 'get',
    params: resume_id ? { resume_id } : undefined
  })
}

export const getChatHistory = ({ application_id }) => {
  return service({
    url: '/api/recruit/chat/history',
    method: 'get',
    params: { application_id }
  })
}

export const sendChatMessage = ({ application_id, message }) => {
  return service({
    url: '/api/recruit/chat/send',
    method: 'post',
    data: { application_id, message }
  })
}
